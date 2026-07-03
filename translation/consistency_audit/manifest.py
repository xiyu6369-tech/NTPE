"""Translation consistency manifest writer for RC.4."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .auditor import TranslationConsistencyAuditor

MANIFEST_NAME = "Translation_Consistency_Audit_RC_04.json"
HASH_NAME = "Translation_Consistency_Hash_RC_04.json"

def build_translation_consistency_manifest(root: str | Path) -> Dict[str, object]:
    root = Path(root)
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    result = TranslationConsistencyAuditor(root).run()
    manifest_path = release / MANIFEST_NAME
    hash_path = release / HASH_NAME
    manifest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    hash_path.write_text(json.dumps(result["hashes"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path), "result": result}

def load_translation_consistency_manifest(path: str | Path) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
