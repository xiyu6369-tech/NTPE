from __future__ import annotations
import json, time
import pytest
import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module
from tests.unit.test_lcr_character_memory_shadow import package

ENABLED={"LCR_SHADOW_KILL_SWITCH":False,"LCR_PRODUCTION_SHADOW":True,"LCR_DUAL_PASS_SEMANTIC_SHADOW":True}
def metadata(**extra):
    base={"chunk_id":"chunk-1","chunk_index":1,"source_hash":"a"*64,"source_char_count":100,"source_language_profile_id":"ko","target_language_profile_id":"zh-Hant","translation_hash":"b"*64,"translation_char_count":90,"quality_signal_summary":{"evidence_complete":True,"dialogue_risk":True,"production_quality_gate_status":"passed"},"context_shadow_summary":{"fingerprint":"c"*64,"unresolved_reference_count":0},"character_shadow_summary":{"fingerprint":"d"*64},"scene_shadow_summary":{},"provider_metadata_summary":{},"retry_metadata_summary":{},"cache_metadata_summary":{},"created_at":"2026-07-18T00:00:00Z"};base.update(extra);return base
def test_default_off_and_alias_priority():
    assert not lcr.resolve_hook_flags({"LCR_PRODUCTION_SHADOW":True,"LCR_SHADOW_KILL_SWITCH":False})[lcr.DUAL_PASS_SEMANTIC_FLAG]
    assert not lcr.resolve_hook_flags({**ENABLED,"LCR_SHADOW_KILL_SWITCH":True})[lcr.DUAL_PASS_SEMANTIC_FLAG]
    assert lcr.resolve_hook_flags(ENABLED)[lcr.DUAL_PASS_SEMANTIC_FLAG]
def test_snapshot_rejects_content_secrets_paths_and_is_immutable():
    item=lcr.build_dual_pass_semantic_shadow_input(metadata())
    assert "source_text" not in repr(item) and "translation_text" not in repr(item)
    for key in ("source_text","prompt","api_key","output_path"):
        with pytest.raises(ValueError):lcr.build_dual_pass_semantic_shadow_input(metadata(**{key:"bad"}))
def test_deterministic_planning_and_synthetic_semantic_api():
    first=lcr.evaluate_dual_pass_semantic_shadow(lcr.build_dual_pass_semantic_shadow_input(metadata()))
    second=lcr.evaluate_dual_pass_semantic_shadow(lcr.build_dual_pass_semantic_shadow_input(metadata()))
    assert first==second and first.mode=="dual_pass_full" and first.semantic_result=="not_applicable"
    synthetic=lcr.evaluate_dual_pass_semantic_shadow(lcr.build_dual_pass_semantic_shadow_input(metadata(synthetic_semantic_fixture={"controlled_synthetic":True,"source":"A 1","draft":"A 1","polish":"A 1","scope_type":"full_chunk"})))
    assert synthetic.semantic_result=="would_accept_polish" and synthetic.provider_executed is False
def test_blocked_and_insufficient_evidence_fail_closed():
    blocked=lcr.evaluate_dual_pass_semantic_shadow(lcr.build_dual_pass_semantic_shadow_input(metadata(translation_char_count=0)))
    insufficient=lcr.evaluate_dual_pass_semantic_shadow(lcr.build_dual_pass_semantic_shadow_input(metadata(quality_signal_summary={})))
    assert blocked.mode=="blocked" and blocked.semantic_result=="would_block"
    assert insufficient.eligibility=="insufficient_evidence" and insufficient.mode=="blocked"
def test_hook_is_read_only_and_metadata_unavailable():
    original=package("ko");before=json.dumps(original,sort_keys=True)
    missing=lcr.run_read_only_lcr_shadow_hook(original,feature_flags=ENABLED)
    result=lcr.run_read_only_lcr_shadow_hook(original,feature_flags=ENABLED,dual_pass_semantic_metadata=metadata())
    assert missing.evidence.dual_pass_semantic.status=="metadata_unavailable"
    assert result.evidence.dual_pass_semantic and result.before_hash==result.after_hash
    assert result.prompt_before_hash==result.prompt_after_hash and result.provider_identity_before==result.provider_identity_after
    assert json.dumps(original,sort_keys=True)==before
def test_timeout_discards_late_result(monkeypatch):
    assert lcr.wait_for_shadow_idle(1)
    original=hook_module.evaluate_dual_pass_semantic_shadow
    def slow(*a,**k):time.sleep(.2);return original(*a,**k)
    monkeypatch.setattr(hook_module,"evaluate_dual_pass_semantic_shadow",slow);sink=lcr.InMemoryEvidenceSink();started=time.perf_counter()
    result=lcr.run_read_only_lcr_shadow_hook(package("ko"),feature_flags=ENABLED,dual_pass_semantic_metadata=metadata(),evidence_sink=sink)
    assert (time.perf_counter()-started)*1000<50 and result.status=="timed_out" and not sink.records
    assert lcr.wait_for_shadow_idle(1) and not sink.records
def test_activation_gate_never_authorizes_production():
    keys=("single_production_hook_unchanged","production_wrapper_unchanged","dual_pass_semantic_flag_default_false","kill_switch_default_true","immutable_snapshot_verified","prompt_unchanged","provider_unchanged","retry_unchanged","resume_unchanged","output_unchanged","cache_unchanged","stores_unchanged","provider_requests_zero","network_requests_zero","draft_generated_false","polish_generated_false","translation_replaced_false","deadline_isolation_pass","late_result_writes_zero","worker_bounded","queue_bounded","security_pass","all_regressions_pass","manual_approval_present")
    gate=lcr.evaluate_dual_pass_semantic_shadow_gate({x:True for x in keys})
    assert gate.status=="ready_for_bounded_dual_pass_pilot" and not gate.active_production_authorized
