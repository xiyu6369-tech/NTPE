from core.translation_quality_integration_v72.prompt_contract import scan_dynamic_section, serialize_candidate_prompt, verify_candidate_prompt

SOURCE = "\uc601\ud76c\uac00 \ub9d0\ud588\ub2e4."
BASE = "\u53ea\u8f38\u51fa\u7e41\u9ad4\u4e2d\u6587\u8b6f\u6587\n\u3010Korean\u3011\n" + SOURCE + "\n\u3010Output\u3011\u76f4\u51fa\u8b6f\u6587"

def test_reference_precedes_contiguous_source_boundary():
    prompt, result = serialize_candidate_prompt(BASE, SOURCE, "[Character] canonical name")
    assert result.valid
    assert prompt.index("[Translation Reference - Do Not Output]") < prompt.index("\u3010Korean\u3011\n" + SOURCE)
    assert verify_candidate_prompt(prompt, SOURCE).valid

def test_dynamic_markers_fail_closed():
    assert "korean-marker" in scan_dynamic_section("\u3010Korean\u3011", SOURCE)
    _, result = serialize_candidate_prompt(BASE, SOURCE, "Translation: bad")
    assert not result.valid and "translation-label-ascii" in result.violations

def test_exact_source_cannot_enter_reference():
    assert "exact-source-in-reference" in scan_dynamic_section(SOURCE, SOURCE)
