import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.literary import normalize_literary_style

print('NTPE TER-v1.6 Semantic Guard Integration Test')
print('=============================================')

text = (
    '伊萊輕笑著說：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。'
    '鄭泰義就站在那裡，直到伊萊轉過彎角，完全消失在視線中為止。'
    '等伊萊徹底消失在視線裡，鄭泰義就靠在牆上，滑坐在地上。'
)
out = normalize_literary_style(text)
assert '留下了鄭泰義一個' not in out
assert out.count('消失在視線') == 1
assert '才靠在牆上' in out
print('PASS')
