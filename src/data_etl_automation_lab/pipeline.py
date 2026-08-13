from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy import delete, func, select

from .database import Base, create_engine_for_url, database_backend, default_database_url
from .models import Device, EventRecord


VALID_STATUSES = {"online", "degraded", "offline"}


@dataclass
class EtlMetrics:
    records_received: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicated_records: int = 0
    processed_records: int = 0
    database_backend: str = ""
    status_counts: dict[str, int] = field(default_factory=dict)
    invalid_details: list[dict] = field(default_factory=list)


def run(events_csv: Path, devices_json: Path, output_dir: Path, database_url: str | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    database_url = database_url or default_database_url(output_dir)
    devices = {item["device_id"]: item for item in json.loads(devices_json.read_text(encoding="utf-8"))}
    rows = list(csv.DictReader(events_csv.read_text(encoding="utf-8").splitlines()))
    metrics = EtlMetrics(records_received=len(rows), database_backend=database_backend(database_url))

    seen_event_ids: set[str] = set()
    valid_events: list[dict] = []
    for row_number, row in enumerate(rows, start=2):
        normalized = normalize_row(row)
        error = validate_row(normalized, devices, seen_event_ids)
        if error == "duplicate_event_id":
            metrics.duplicated_records += 1
            metrics.invalid_details.append({"row": row_number, "event_id": normalized.get("event_id"), "reason": error})
            continue
        if error:
            metrics.invalid_records += 1
            metrics.invalid_details.append({"row": row_number, "event_id": normalized.get("event_id"), "reason": error})
            continue

        seen_event_ids.add(normalized["event_id"])
        valid_events.append(transform_row(normalized, devices[normalized["device_id"]]))

    metrics.valid_records = len(valid_events)

    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as session:
        session.execute(delete(EventRecord))
        session.execute(delete(Device))
        session.add_all(Device(device_id=device["device_id"], group=device["group"]) for device in devices.values())
        session.flush()
        session.add_all(EventRecord(**event) for event in valid_events)
        session.commit()

        metrics.processed_records = session.scalar(select(func.count(EventRecord.id))) or 0
        metrics.status_counts = dict(session.execute(select(EventRecord.status, func.count()).group_by(EventRecord.status)).all())

    report = asdict(metrics)
    write_outputs(output_dir, report)
    return report


def normalize_row(row: dict) -> dict:
    return {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}


def validate_row(row: dict, devices: dict[str, dict], seen_event_ids: set[str]) -> str | None:
    event_id = row.get("event_id", "")
    if not event_id:
        return "missing_event_id"
    if event_id in seen_event_ids:
        return "duplicate_event_id"
    if row.get("device_id") not in devices:
        return "unknown_device"
    if row.get("status") not in VALID_STATUSES:
        return "invalid_status"
    try:
        battery_level = int(row.get("battery_level", ""))
        signal_level = int(row.get("signal_level", ""))
    except ValueError:
        return "invalid_numeric_value"
    if not (0 <= battery_level <= 100 and 0 <= signal_level <= 100):
        return "metric_out_of_range"
    return None


def transform_row(row: dict, device: dict) -> dict:
    battery_level = int(row["battery_level"])
    signal_level = int(row["signal_level"])
    return {
        "event_id": row["event_id"],
        "device_id": row["device_id"],
        "group": device["group"],
        "status": row["status"],
        "battery_level": battery_level,
        "signal_level": signal_level,
        "health_score": round((battery_level + signal_level) / 2),
    }


def write_outputs(output_dir: Path, report: dict) -> None:
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "invalid_records.json").write_text(json.dumps(report["invalid_details"], indent=2), encoding="utf-8")
    manifest = {
        "outputs": ["summary.json", "invalid_records.json"],
        "database_backend": report["database_backend"],
        "tables": ["devices", "event_records"],
    }
    if report["database_backend"] == "sqlite":
        manifest["outputs"].append("etl_lab.db")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
