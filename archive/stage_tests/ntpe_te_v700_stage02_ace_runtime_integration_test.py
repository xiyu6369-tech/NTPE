from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from core.adaptive_context_integration import INTEGRATION_VERSION, integrate_adaptive_context, resolve_mode


def main() -> int:
    assert INTEGRATION_VERSION == '7.0.0-stage02'
    payload = {'system':'fixed','source':'原文','context':{
        'locked_glossary': {'content':'정태의 -> 鄭泰義', 'required':True, 'locked':True},
        'previous_chunk_tail': '他站在窗邊。街上沒有行人。鐘聲從遠處傳來。',
        'dialogue_context': '「你真的要走嗎？」\n「是的。」',
        'irrelevant_other': 'x' * 400,
    }}
    disabled = integrate_adaptive_context(payload, mode='disabled', requested_context_tokens=30)
    assert disabled.prompt_payload_hash == disabled.baseline_payload_hash
    assert not disabled.used_ace and disabled.effective_context == payload['context']
    shadow = integrate_adaptive_context(payload, mode='shadow', requested_context_tokens=30)
    assert shadow.prompt_payload_hash == shadow.baseline_payload_hash
    assert shadow.prompt_payload == payload and not shadow.used_ace
    invalid = integrate_adaptive_context(payload, mode='banana')
    assert invalid.effective_mode == 'disabled' and invalid.fallback_used
    assert invalid.fallback_reasons == ('invalid-mode:banana',)
    active = integrate_adaptive_context(payload, mode='active', requested_context_tokens=30)
    assert active.fallback_used or active.used_ace
    assert active.metrics['raw_context_retained'] is False
    assert '鄭泰義' not in repr(active.metrics)
    overflow = integrate_adaptive_context(payload, mode='active', requested_context_tokens=1)
    assert overflow.fallback_used and not overflow.used_ace
    assert overflow.prompt_payload_hash == overflow.baseline_payload_hash
    old = os.environ.get('NTPE_TE_V7_ACE_MODE')
    try:
        os.environ['NTPE_TE_V7_ACE_MODE'] = 'shadow'
        assert resolve_mode()[0] == 'shadow'
    finally:
        if old is None: os.environ.pop('NTPE_TE_V7_ACE_MODE', None)
        else: os.environ['NTPE_TE_V7_ACE_MODE'] = old
    root = Path(__file__).resolve().parent
    manifest = json.loads((root/'manifests/te_v700_stage02_ace_runtime_integration_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['integrity']['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
    print('TE v7.0 Stage 02 ACE Runtime Integration ALL PASS')
    return 0

if __name__ == '__main__': raise SystemExit(main())
