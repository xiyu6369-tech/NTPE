from __future__ import annotations

from pathlib import Path

from core.translation_runtime import TranslationRuntime
from core.translation_session import TranslationSessionManager, load_checkpoint


def test_translation_session_create_manifest_and_checkpoint(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    created = runtime.create_session(mode="txt", input_source="input.txt", output_target="output.txt", metadata={"stage": "05"})

    assert created["status"] == "success"
    session_id = created["session_id"]
    assert created["manifest"]["session_version"] == "1.2-professional-stage-05"
    assert created["manifest"]["compatibility_floor"] == "1.1-lts-stable"

    manifest_path = tmp_path / ".ntpe_sessions" / session_id / "session_manifest.json"
    checkpoint_path = tmp_path / ".ntpe_sessions" / session_id / "session_checkpoint.json"
    assert manifest_path.exists()
    assert checkpoint_path.exists()

    checkpoint = load_checkpoint(tmp_path, session_id)
    assert checkpoint is not None
    assert checkpoint.status == "created"
    assert checkpoint.cursor["resume_token"] == session_id


def test_session_execute_wraps_runtime_operation(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    manager = TranslationSessionManager(tmp_path, runtime)
    session = manager.create_session(mode="package", input_source="sample-package.json")

    result = session.execute(lambda: {"status": "success", "chunk_total": 3, "output_path": "out.txt"})

    assert result["status"] == "success"
    assert result["statistics"]["chunk_total"] == 3
    checkpoint = manager.get_checkpoint(session.session_id)
    assert checkpoint is not None
    assert checkpoint["status"] == "success"
    assert checkpoint["cursor"]["progress_current"] == 3
    assert checkpoint["cursor"]["progress_total"] == 3


def test_runtime_session_contract_and_listing(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    compatibility = runtime.validate_compatibility()

    assert compatibility["status"] == "success"
    assert "create_session" not in compatibility["missing_entrypoints"]
    assert any(item["name"] == "translation_session" for item in compatibility["capabilities"])

    runtime.create_session(mode="batch", input_source="input", output_target="output")
    listing = runtime.list_sessions()
    assert listing["status"] == "success"
    assert listing["total"] == 1
