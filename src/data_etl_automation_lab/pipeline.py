from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


def run(events_csv: Path, devices_json: Path, output_dir: Path) -> dict:
    devices = {item["device_id"]: item for item in json.loads(devices_json.read_text(encoding="utf-8"))}
    events = list(csv.DictReader(events_csv.read_text(encoding="utf-8").splitlines()))
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "etl_lab.db"
    valid_events = []
    for event in events:
        if event["device_id"] not in devices:
            continue
        event["battery_level"] = int(event["battery_level"])
        event["signal_level"] = int(event["signal_level"])
        valid_events.append(event)
    with sqlite3.connect(db_path) as conn:
        conn.execute("create table if not exists events(event_id text, device_id text, status text, battery_level integer, signal_level integer)")
        conn.execute("delete from events")
        conn.executemany(
            "insert into events values (:event_id, :device_id, :status, :battery_level, :signal_level)",
            valid_events,
        )
        status_counts = dict(conn.execute("select status, count(*) from events group by status").fetchall())
    report = {"input_events": len(events), "valid_events": len(valid_events), "status_counts": status_counts}
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps({"outputs": ["etl_lab.db", "summary.json"]}, indent=2), encoding="utf-8")
    return report
