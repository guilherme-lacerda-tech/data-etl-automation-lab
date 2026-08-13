from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_etl_automation_lab.pipeline import transform_row, validate_row, run


def test_pipeline_validates_deduplicates_and_loads(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    report = run(
        root / "data" / "sample" / "events.csv",
        root / "data" / "sample" / "devices.json",
        tmp_path,
        "sqlite+pysqlite:///:memory:",
    )

    assert report["records_received"] == 7
    assert report["valid_records"] == 4
    assert report["invalid_records"] == 2
    assert report["duplicated_records"] == 1
    assert report["processed_records"] == 4
    assert report["status_counts"] == {"degraded": 1, "offline": 1, "online": 2}
    assert (tmp_path / "summary.json").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["tables"] == ["devices", "event_records"]


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"event_id": "", "device_id": "LAB-001", "status": "online", "battery_level": "90", "signal_level": "80"}, "missing_event_id"),
        ({"event_id": "EVT-1", "device_id": "LAB-999", "status": "online", "battery_level": "90", "signal_level": "80"}, "unknown_device"),
        ({"event_id": "EVT-1", "device_id": "LAB-001", "status": "paused", "battery_level": "90", "signal_level": "80"}, "invalid_status"),
        ({"event_id": "EVT-1", "device_id": "LAB-001", "status": "online", "battery_level": "bad", "signal_level": "80"}, "invalid_numeric_value"),
        ({"event_id": "EVT-1", "device_id": "LAB-001", "status": "online", "battery_level": "101", "signal_level": "80"}, "metric_out_of_range"),
    ],
)
def test_validate_row_reports_specific_errors(row: dict, expected: str) -> None:
    devices = {"LAB-001": {"device_id": "LAB-001", "group": "north"}}

    assert validate_row(row, devices, set()) == expected


def test_validate_row_reports_duplicate_event_id() -> None:
    row = {"event_id": "EVT-1", "device_id": "LAB-001", "status": "online", "battery_level": "90", "signal_level": "80"}

    assert validate_row(row, {"LAB-001": {"device_id": "LAB-001", "group": "north"}}, {"EVT-1"}) == "duplicate_event_id"


def test_transform_row_adds_group_and_health_score() -> None:
    transformed = transform_row(
        {"event_id": "EVT-10", "device_id": "LAB-001", "status": "online", "battery_level": "80", "signal_level": "60"},
        {"device_id": "LAB-001", "group": "north"},
    )

    assert transformed["group"] == "north"
    assert transformed["health_score"] == 70
