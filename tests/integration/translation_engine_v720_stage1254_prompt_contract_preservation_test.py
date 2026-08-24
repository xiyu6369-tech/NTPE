from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.translation_quality_integration_v72 import QualityIntegrationFlags, QualityIntegrationRequest, integrate_prompt, verify_candidate_prompt
from core.translation_quality_integration_v72.prompt_contract import REFERENCE_END, REFERENCE_START, serialize_candidate_prompt
from core.translation_quality_provider_canary.framework import _build_prompts

ROOT = Path(__file__).resolve().parents[2]
CASE = json.loads((ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_text(encoding="utf-8"))["cases"][0]
FIXTURES = ROOT / "tests/fixtures/te_v72_canary"
CLAIM = FIXTURES / "execution_claim.json"

def _candidate() -> tuple[str, str, str, dict[str, object]]:
    return _build_prompts(str(CASE["case_id"]), str(CASE["source_text"]))

def test_all_milestone_a_sections_serialize_before_exact_source_boundary() -> None:
    _, baseline, candidate, metadata = _candidate()
    source = str(CASE["source_text"])
    assert all(metadata["flags"][key] for key in ("integration", "character_memory", "context_scene", "naturalness"))
    assert verify_candidate_prompt(candidate, source).valid
    boundary = f"【Korean】\n{source}\n【Output】"
    assert candidate.index(REFERENCE_START) < candidate.index(REFERENCE_END) < candidate.index(boundary)
    assert candidate.count(source) == baseline.count(source) == 1
    for heading in ("【人物一致性記憶", "【目前場景提示】", "【有限上下文連貫提示", "【自然度政策"):
        assert candidate.index(heading) < candidate.index(boundary)

@pytest.mark.parametrize("unsafe", ("【Korean】", "【Output】", "譯文：", "Source:", "Translation:", str(CASE["source_text"])))
def test_unsafe_dynamic_content_is_fail_closed_before_provider_eligibility(unsafe: str) -> None:
    _, baseline, _, _ = _candidate()
    _, verification = serialize_candidate_prompt(baseline, str(CASE["source_text"]), unsafe)
    assert not verification.valid

def test_disabled_path_claim_and_offline_boundaries_remain_unchanged() -> None:
    claim_before = hashlib.sha256(CLAIM.read_bytes()).hexdigest()
    _, baseline, candidate, _ = _candidate()
    source = str(CASE["source_text"])
    disabled = integrate_prompt(baseline, QualityIntegrationRequest(source_text=source, base_prompt_tokens=0, flags=QualityIntegrationFlags()))
    assert disabled.user_prompt == baseline and disabled.section == ""
    assert candidate == _candidate()[2]
    assert hashlib.sha256(CLAIM.read_bytes()).hexdigest() == claim_before
    assert json.loads(CLAIM.read_text(encoding="utf-8"))["claimed"] is True
    generator = (ROOT / "tools/generate_te_v720_stage1254_prompt_contract_preservation.py").read_text(encoding="utf-8")
    for forbidden in ("NvidiaClient", "NVIDIA_API_KEY", "provider_payload", "requests.", "httpx"):
        assert forbidden not in generator
