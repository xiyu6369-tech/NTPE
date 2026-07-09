from pathlib import Path

root = Path(__file__).resolve().parents[2]
assert (root / 'launcher_translate.py').exists()
assert (root / 'lts' / 'txt_translation_runtime.py').exists()
print('TER-v2.1 Smoke            PASS')
print('PASS')
