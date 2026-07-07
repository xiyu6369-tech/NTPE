from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import _provider_model_chain


def check(name, condition):
    print(f"{name:<28} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)

check('Fallback Chain Exists', _provider_model_chain('meta/llama-3.3-70b-instruct')[0] == 'meta/llama-3.3-70b-instruct')
print('PASS')
