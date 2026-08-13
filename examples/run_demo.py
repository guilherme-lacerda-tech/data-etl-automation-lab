from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_etl_automation_lab.pipeline import run


output_dir = ROOT / "data" / "generated"
result = run(ROOT / "data" / "sample" / "events.csv", ROOT / "data" / "sample" / "devices.json", output_dir)
print(result)
