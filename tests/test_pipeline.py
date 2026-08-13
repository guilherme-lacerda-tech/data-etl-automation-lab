from __future__ import annotations

from pathlib import Path

from data_etl_automation_lab.pipeline import run


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
    assert (tmp_path / "manifest.json").exists()
