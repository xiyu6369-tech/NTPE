import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.literary import normalize_literary_style

print('NTPE TER-v1.6 Semantic Guard Smoke Test')
print('=======================================')

out = normalize_literary_style('伊萊輕笑著說：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。')
assert '留下了鄭泰義一個' not in out
assert '只答了一句「當然」' in out
print('PASS')
