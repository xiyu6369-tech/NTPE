from core.translation_runtime import TranslationRuntime


def test_plugin_architecture_smoke(tmp_path):
    runtime = TranslationRuntime(root=tmp_path)
    manifest = runtime.save_plugin_manifest("smoke-plugin-manifest")
    assert manifest["status"] == "success"
    assert manifest["manifest"]["version"] == "1.2-professional-stage-08"
    assert runtime.validate_plugins()["status"] == "success"
