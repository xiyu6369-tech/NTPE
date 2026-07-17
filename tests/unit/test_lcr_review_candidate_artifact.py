import json
from pathlib import Path

import pytest

from core.lcr_production_shadow_hook.review_candidate_artifact import build_review_artifact, write_review_artifact


def test_artifact_is_immutable_atomic_and_deterministic(tmp_path):
    artifact = build_review_artifact({"candidate_text": "候選", "source_hash": "a" * 64})
    with pytest.raises(TypeError): artifact["candidate_text"] = "changed"
    one = write_review_artifact(tmp_path / "isolated", artifact)
    two = write_review_artifact(tmp_path / "isolated", artifact)
    assert one == two and not list((tmp_path / "isolated").glob("*.tmp-*"))
    assert json.loads(Path(one[0]).read_text(encoding="utf-8"))["candidate_text"] == "候選"


@pytest.mark.parametrize("field", ["api_key", "secret", "prompt", "full_document", "filesystem_path", "resume_state"])
def test_forbidden_sensitive_fields_are_rejected(field):
    with pytest.raises(ValueError): build_review_artifact({field: "value"})


def test_writer_uses_digest_filename_not_user_path(tmp_path):
    path, _ = write_review_artifact(tmp_path, build_review_artifact({"chunk_id": "../../escape", "candidate_text": "x"}))
    assert Path(path).parent == tmp_path.resolve() and ".." not in Path(path).name
