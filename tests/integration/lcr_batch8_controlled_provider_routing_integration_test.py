from __future__ import annotations
import json,subprocess
from pathlib import Path
import core.controlled_provider_routing as pr
import core.multilingual_profiles as mp
from tests.unit.test_controlled_provider_routing import routing_input,evidence
ROOT=Path(__file__).resolve().parents[2]

def test_batch7_profiles_feed_routing_identity_without_language_inference():
    for language in ("ko","ja","en"):
        lp=mp.select_language_profile(language,"zh-Hant").profile;item=routing_input(source_language=language,language_profile_id=lp.profile_id,language_profile_version=lp.profile_version,language_profile_fingerprint=lp.fingerprint)
        decision=pr.select_provider_route(item,pr.PROVIDER_PROFILES);identity=pr.build_provider_route_identity(item,pr.NVIDIA_PROFILE,pr.DEFAULT_ROUTING_POLICY)
        assert decision.decision=="use_primary" and identity["fields"]["language_profile_fingerprint"]==lp.fingerprint

def test_dual_pass_cost_and_batch6_requirement_are_bounded():
    result=pr.select_provider_route(routing_input(translation_mode="dual_pass",draft_required=True,polish_required=True),pr.PROVIDER_PROFILES)
    assert result.estimated_requests==2 and result.maximum_requests==2
    blocked=pr.select_provider_route(routing_input(semantic_verification_available=False),pr.PROVIDER_PROFILES)
    assert blocked.decision=="blocked"

def test_historical_timeout_is_evidence_not_health_probe():
    payload=json.loads((ROOT/"tests/fixtures/lcr_batch8/historical_provider_failures.json").read_text(encoding="utf-8"))
    assert payload["historical_evidence"] and payload["current_health_unknown"] and payload["not_executable_request"]
    assert any(x.get("timeout_seconds")==180 for x in payload["items"])

def test_cross_provider_polish_requires_manual_approval_and_semantics():
    item=routing_input(manual_approval_granted=False,translation_mode="selective_polish",verified_draft_available=True,draft_required=False,polish_required=True)
    fallback=pr.evaluate_fallback_eligibility(item,pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence())
    assert fallback.status=="manual_approval_required" and not fallback.fallback_allowed

def test_execution_and_security_boundary():
    item=routing_input();decision=pr.select_provider_route(item,pr.PROVIDER_PROFILES);plan=pr.build_provider_execution_plan(item,decision,pr.NVIDIA_PROFILE);ev=pr.build_routing_evidence(item,decision)
    assert plan.prepare_only and not plan.executed and plan.network_requests==0 and ev.routing_decision_id.startswith("route-")
    assert not any(key in asdict for asdict in (repr(plan).lower(),repr(ev).lower()) for key in ("authorization:","api_key=","raw_provider_response"))

def test_production_and_frozen_core_allowlist():
    lines=subprocess.run(["git","status","--short"],cwd=ROOT,check=True,capture_output=True,text=True,encoding="utf-8").stdout.splitlines();allowed=("core/controlled_provider_routing/","tests/unit/test_controlled_provider_routing.py","tests/integration/lcr_batch8_controlled_provider_routing_integration_test.py","tests/fixtures/lcr_batch8/","ntpe_lcr_batch8_controlled_provider_routing_test.py","audits/legacy_capability_recovery/batch8/","NTPE_LCR_BATCH8_AUDIT.zip")
    assert all(line[3:].replace("\\","/").strip('"').startswith(allowed) for line in lines)
