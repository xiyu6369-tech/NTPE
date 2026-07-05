from __future__ import annotations

from core.translation_runtime import TranslationRuntime


def test_pipeline_smoke(tmp_path):
    runtime = TranslationRuntime(root=tmp_path)
    assert runtime.validate_pipeline()["status"] == "success"
    assert runtime.execute_pipeline({"smoke": True})["status"] == "success"
