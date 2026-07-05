from pathlib import Path

from core.translation_runtime import TranslationRuntime, build_runtime_contract, validate_runtime_contract


def test_runtime_contract_declares_stage_02_surface():
    root = Path(__file__).resolve().parents[2]
    runtime = TranslationRuntime(root=root)
    contract = runtime.describe()
    assert contract["version"] == "1.2-professional-stage-02"
    assert contract["compatibility_floor"] == "1.1-lts-stable"
    assert "translate_txt" in contract["entrypoints"]
    assert "translate_batch" in contract["entrypoints"]
    assert contract["pipeline"] == [
        "Encoding",
        "Chunk",
        "Context",
        "Glossary",
        "Character Memory",
        "Prompt Builder",
        "AI Provider",
        "QA",
        "Taiwan Formatter",
        "Output",
    ]


def test_runtime_contract_validation_passes():
    root = Path(__file__).resolve().parents[2]
    runtime = TranslationRuntime(root=root)
    result = runtime.validate_compatibility()
    assert result["status"] == "success"
    assert result["missing_entrypoints"] == []
    assert any(item["name"] == "lts_compatibility" for item in result["capabilities"])


def test_runtime_contract_builder_is_exported():
    root = Path(__file__).resolve().parents[2]
    contract = build_runtime_contract("x", root)
    assert contract.to_dict()["root"] == str(root)
    assert validate_runtime_contract(TranslationRuntime(root=root))["status"] == "success"
