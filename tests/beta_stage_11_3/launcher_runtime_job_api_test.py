"""Launcher for Stage-11.3 Runtime Job API tests."""
from __future__ import annotations
from pathlib import Path
import runpy
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
runpy.run_path(str(Path(__file__).with_name("runtime_job_api_test.py")), run_name="__main__")
