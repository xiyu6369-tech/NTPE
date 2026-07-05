from __future__ import annotations

from core.translation_runtime import TranslationRuntime


def test_resource_manager_smoke(tmp_path):
    runtime = TranslationRuntime(root=tmp_path)
    resources = runtime.describe_resources()
    pipeline = runtime.describe_pipeline()
    assert resources["status"] == "success"
    assert pipeline["status"] == "success"
    assert pipeline["resources"]["status"] == "success"
