import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.literary import normalize_literary_style
from lts.txt_translation_runtime import detect_quality_lock_violations

print('NTPE TER-v2.0 Integration Test')
text = '伊萊笑著回答：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。鄭泰義就站在原地，直到伊萊轉過彎角，徹底消失在視線裡。等伊萊完全消失後，鄭泰義就靠在牆上，滑坐在地上。'
out = normalize_literary_style(text)
assert '留下了鄭泰義' not in out
assert out.count('消失在視線') <= 1
assert detect_quality_lock_violations(out) == []
print('PASS')
