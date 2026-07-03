from pathlib import Path
from translation.consistency_audit import build_translation_consistency_manifest, load_translation_consistency_manifest

def test_translation_consistency_manifest_written(tmp_path):
    output = build_translation_consistency_manifest(tmp_path)
    manifest_path = Path(output["manifest_path"])
    hash_path = Path(output["hash_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    manifest = load_translation_consistency_manifest(manifest_path)
    assert manifest["passed"] is True
    assert manifest["stage"] == "RC.4"
