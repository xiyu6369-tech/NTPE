from core.adaptive_context_integration import integrate_adaptive_context

def _payload():
    return {'prompt':'unchanged','context':{
        'glossary': {'content':'일라이 -> 伊萊', 'required':True, 'locked':True},
        'narrative_context':'他走進房間。燈光很暗。窗外正在下雨。',
        'other':'redundant ' * 100,
    }}

def test_disabled_and_shadow_payload_equivalence():
    payload = _payload()
    disabled = integrate_adaptive_context(payload, mode='disabled', requested_context_tokens=25)
    shadow = integrate_adaptive_context(payload, mode='shadow', requested_context_tokens=25)
    assert disabled.prompt_payload_hash == disabled.baseline_payload_hash
    assert shadow.prompt_payload_hash == shadow.baseline_payload_hash
    assert dict(shadow.prompt_payload) == payload

def test_active_admission_or_full_fallback_only():
    payload = _payload()
    result = integrate_adaptive_context(payload, mode='active', requested_context_tokens=25)
    if result.used_ace:
        assert not result.fallback_used
        assert result.prompt_payload_hash != result.baseline_payload_hash
    else:
        assert result.fallback_used
        assert result.prompt_payload_hash == result.baseline_payload_hash
        assert dict(result.effective_context) == payload['context']
