from pathlib import Path

root = Path(__file__).resolve().parents[2]
text = (root / 'ntpe_production_translate.py').read_text(encoding='utf-8')
runtime = (root / 'lts' / 'txt_translation_runtime.py').read_text(encoding='utf-8')
assert '--fallback-models' in text
assert 'NTPE_FALLBACK_MODELS' in text
assert 'DEGRADED' in runtime
assert 'provider fast-fail: model degraded' in runtime
print('TER-v2.1 Integration      PASS')
print('PASS')
