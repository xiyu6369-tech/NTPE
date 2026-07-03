"""Regression manifest writer."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .runner import RegressionRunner

MANIFEST_NAME = "Regression_Baseline_RC_01.json"
HASH_NAME = "Regression_Hash_RC_01.json"
COMPATIBILITY_NAME = "Compatibility_RC_01.json"

def build_regression_manifest(root: str | Path) -> Dict[str, object]:
    root = Path(root)
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    result = RegressionRunner(root).run()
    manifest_path = release / MANIFEST_NAME
    hash_path = release / HASH_NAME
    compatibility_path = release / COMPATIBILITY_NAME
    manifest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    hash_path.write_text(json.dumps(result["hashes"], indent=2, ensure_ascii=False), encoding="utf-8")
    compatibility_path.write_text(json.dumps(result["compatibility"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path), "compatibility_path": str(compatibility_path), "result": result}

def load_regression_manifest(path: str | Path) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
