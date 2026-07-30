from __future__ import annotations

import json
from pathlib import Path

from core.translation_quality_integration_v72 import QualityIntegrationFlags, QualityIntegrationRequest, integrate_prompt, verify_candidate_prompt
from core.translation_quality_integration_v72.prompt_contract import REFERENCE_START, serialize_candidate_prompt
from core.translation_quality_provider_canary.framework import _build_prompts
from tools.generate_te_v720_stage1254_prompt_contract_preservation import ARTIFACT_ROOT, MANIFEST, RELEASE, build_outputs

ROOT = Path(__file__).resolve().parent
CASE = json.loads((ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_text(encoding="utf-8"))["cases"][0]

def test_stage1254_root_acceptance() -> None:
    source = str(CASE["source_text"])
    _, baseline, candidate, _ = _build_prompts(str(CASE["case_id"]), source)
    verification = verify_candidate_prompt(candidate, source)
    assert verification.valid
    assert candidate.index(REFERENCE_START) < candidate.index(f"【Korean】\n{source}")
    assert f"【Korean】\n{source}\n【Output】" in candidate and candidate.count(source) == 1
    _, invalid = serialize_candidate_prompt(baseline, source, "Translation: forbidden")
    assert not invalid.valid and "translation-label-ascii" in invalid.violations
    disabled = integrate_prompt(baseline, QualityIntegrationRequest(source_text=source, base_prompt_tokens=0, flags=QualityIntegrationFlags()))
    assert disabled.user_prompt == baseline and disabled.section == ""
    artifacts, expected_manifest = build_outputs()
    assert set(artifacts) == {path.name for path in ARTIFACT_ROOT.iterdir() if path.is_file()}
    assert all((ARTIFACT_ROOT / name).read_bytes() == value for name, value in artifacts.items())
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest == expected_manifest and RELEASE.is_file()
    assert manifest["activation_gate"] == "translation_quality_integration_ready_for_controlled_canary"
    assert manifest["provider_requests_added"] == manifest["network_requests_added"] == manifest["retry_added"] == 0
    assert manifest["fallback"] is False and manifest["execution_claim_replayed"] is False
    assert all(manifest[key] is False for key in ("active_production_authorized", "automatic_rollout_authorized", "formal_output_replacement_authorized", "production_authorized"))

def main() -> int:
    test_stage1254_root_acceptance()
    print("TE_V720_STAGE1254_ROOT_ACCEPTANCE=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
