from __future__ import annotations

from pathlib import Path as _NtpeVerificationPath

_ntpe_verification_root = next(
    parent for parent in _NtpeVerificationPath(__file__).resolve().parents if parent.name == "verification"
)
exec((_ntpe_verification_root / "_bootstrap.py").read_text(encoding="utf-8"), globals())
activate_verification(_ntpe_verification_root)

import json
from dataclasses import replace

from core.launcher_product.command_builder import build_translation_command
from core.launcher_product.config import load_launcher_config
from core.launcher_product.languages import detect_source_language
from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog
from ui.translation_launcher.state import build_window_model


ROOT = verification_project_root()
ARTIFACT_DIRECTORY = ROOT / "artifacts/ntpe_v20_stage1_translation_launcher_product_foundation"


def _load_artifact(name: str) -> object:
    return json.loads((ARTIFACT_DIRECTORY / name).read_text(encoding="utf-8"))


def test_ntpe_v20_stage1_translation_launcher_product_foundation() -> None:
    required_artifacts = {
        "COMMAND_BUILDER_EVIDENCE.json",
        "GUI_SMOKE_EVIDENCE.json",
        "LANGUAGE_DETECTION_EVIDENCE.json",
        "MODEL_CATALOG.json",
        "PROVIDER_CATALOG.json",
        "VALIDATION_REPORT.json",
    }
    assert required_artifacts == {path.name for path in ARTIFACT_DIRECTORY.glob("*.json")}

    providers = provider_catalog({})
    models = model_catalog()
    assert [provider.provider_id for provider in providers] == ["nvidia", "gemini"]
    assert [model.model_id for model in models] == [
        "meta/llama-3.3-70b-instruct",
        "gemini-2.5-flash",
    ]
    assert all(not provider.configured for provider in providers)
    assert detect_source_language("그녀는 조용히 책을 덮었다.").language == "ko"
    assert detect_source_language("彼女は静かに本を閉じた。").language == "ja"

    config = replace(
        load_launcher_config(),
        input_path="tests/fixtures/launcher_product/korean_sample.txt",
        output_directory="output",
        dry_run=True,
    )
    command = build_translation_command(config, environment={"NVIDIA_API_KEY": "configured"})
    assert command.validation_result.ready is True
    assert command.argument_list[:3] == ("python", "launcher_translate.py", "txt")
    assert not {"--input", "--output", "--overwrite", "--provider"}.intersection(command.argument_list)
    assert build_window_model().start_enabled is False

    command_evidence = _load_artifact("COMMAND_BUILDER_EVIDENCE.json")
    gui_evidence = _load_artifact("GUI_SMOKE_EVIDENCE.json")
    validation_report = _load_artifact("VALIDATION_REPORT.json")
    assert command_evidence["subprocess_started"] is False
    assert gui_evidence["translation_executions"] == 0
    assert validation_report["provider_requests"] == 0
    assert validation_report["network_requests"] == 0
    assert validation_report["translation_executions"] == 0
    assert (ROOT / "ntpe_launcher.py").is_file()
    assert (ROOT / "launcher_translate.py").is_file()


if __name__ == "__main__":
    test_ntpe_v20_stage1_translation_launcher_product_foundation()
    print("NTPE_V20_STAGE1_TRANSLATION_LAUNCHER_PRODUCT_FOUNDATION=PASS")
