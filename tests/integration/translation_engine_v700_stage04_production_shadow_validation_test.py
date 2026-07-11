from __future__ import annotations
import os
from core.adaptive_context_production_validation import build_production_shadow_report, production_shadow_session
from core.adaptive_context_runtime_shadow.model import ShadowAuditRecord


def _record(eq=True):
    return ShadowAuditRecord(version='7.0.0-stage03', package_id='pkg', mode='shadow', payload_hash_before='a', payload_hash_after='a' if eq else 'b', payload_equivalent=eq, provider_calls_added=0, metrics={'baseline_context_tokens':100,'ace_context_tokens':70,'admissible':True,'fallback_required':False,'ace_build_latency_ms':2.5})


def test_report_passes_only_when_payloads_are_equivalent():
    report = build_production_shadow_report({'status':'success'}, records=[_record()], provider_execution_requested=False)
    assert report.ready and report.estimated_tokens_saved == 30
    failed = build_production_shadow_report({'status':'success'}, records=[_record(False)], provider_execution_requested=False)
    assert not failed.ready and failed.payload_mismatch_records == 1


def test_shadow_session_restores_environment(monkeypatch):
    monkeypatch.setenv('NTPE_TE_V7_ACE_MODE','disabled')
    with production_shadow_session(audit_path='x.jsonl'):
        assert os.environ['NTPE_TE_V7_ACE_MODE'] == 'shadow'
        assert os.environ['NTPE_TE_V7_ACE_SHADOW_AUDIT'] == 'x.jsonl'
    assert os.environ['NTPE_TE_V7_ACE_MODE'] == 'disabled'
