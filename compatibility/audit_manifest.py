"""Compatibility audit manifest writer."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .audit_runner import CompatibilityAuditRunner

MANIFEST_NAME = "Compatibility_Audit_RC_02.json"
HASH_NAME = "Compatibility_Audit_Hash_RC_02.json"


def build_compatibility_audit_manifest(root: str | Path) -> Dict[str, object]:
    root = Path(root)
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    result = CompatibilityAuditRunner(root).run()
    manifest_path = release / MANIFEST_NAME
    hash_path = release / HASH_NAME
    manifest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    hash_path.write_text(json.dumps(result["hashes"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path), "result": result}


def load_compatibility_audit_manifest(path: str | Path) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
