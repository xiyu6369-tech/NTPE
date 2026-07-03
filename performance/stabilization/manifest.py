"""Performance stabilization manifest writer."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .stabilizer import PerformanceStabilizer

MANIFEST_NAME = "Performance_Stabilization_RC_03.json"
HASH_NAME = "Performance_Stabilization_Hash_RC_03.json"

def build_performance_stabilization_manifest(root: str | Path) -> Dict[str, object]:
    root = Path(root)
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    result = PerformanceStabilizer(root).run()
    manifest_path = release / MANIFEST_NAME
    hash_path = release / HASH_NAME
    manifest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    hash_path.write_text(json.dumps(result["hashes"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path), "result": result}

def load_performance_stabilization_manifest(path: str | Path) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
