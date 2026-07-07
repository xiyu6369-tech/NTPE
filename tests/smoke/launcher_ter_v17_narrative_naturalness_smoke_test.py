import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.literary import normalize_literary_style

print('NTPE TER-v1.7 Narrative Naturalness Smoke Test')
print('==============================================')

out = normalize_literary_style('鄭泰義叫住了想要轉身離開的伊萊，伊萊挑了挑眉，轉頭看向鄭泰義。')
assert '正要轉身離去' in out
assert '轉頭看了過來' in out
print('PASS')
