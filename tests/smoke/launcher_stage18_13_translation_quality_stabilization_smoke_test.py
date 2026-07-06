import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import load_locked_dictionary, apply_locked_dictionary

locked = load_locked_dictionary(ROOT)
assert locked.get('정태의') == '鄭泰義'
assert apply_locked_dictionary('정태의 定泰義', locked) == '鄭泰義 鄭泰義'
print('PASS')
