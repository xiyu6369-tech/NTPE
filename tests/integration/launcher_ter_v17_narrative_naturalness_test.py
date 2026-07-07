import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.literary import normalize_literary_style

print('NTPE TER-v1.7 Narrative Naturalness Integration Test')
print('====================================================')

text = (
    '鄭泰義叫住了想要轉身離開的伊萊，伊萊挑了挑眉，轉頭看向鄭泰義。'
    '鄭泰義心情沉重地瞪了伊萊一會兒。'
    '突然之間，幾十年的疲勞感覺像洪水一樣湧了上來。'
)
out = normalize_literary_style(text)
assert '正要轉身離去' in out
assert '轉頭看了過來' in out
assert '神情沉重地瞪著他看了一會兒' in out
assert '彷彿積壓了數十年的疲憊一口氣湧了上來' in out
print('PASS')
