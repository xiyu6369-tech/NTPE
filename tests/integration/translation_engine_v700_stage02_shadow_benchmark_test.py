from core.adaptive_context_integration import integrate_adaptive_context

def test_shadow_is_deterministic_and_redacted():
    payload = {'source':'abc','context':{'previous_chunk_tail':'第一句。第二句。','other':'z'*200}}
    a = integrate_adaptive_context(payload, mode='shadow', requested_context_tokens=8)
    b = integrate_adaptive_context(payload, mode='shadow', requested_context_tokens=8)
    comparable_a = {k:v for k,v in a.metrics.items() if k != 'ace_build_latency_ms'}
    comparable_b = {k:v for k,v in b.metrics.items() if k != 'ace_build_latency_ms'}
    assert comparable_a == comparable_b
    assert a.prompt_payload_hash == a.baseline_payload_hash
    assert '第一句' not in repr(a.metrics)
