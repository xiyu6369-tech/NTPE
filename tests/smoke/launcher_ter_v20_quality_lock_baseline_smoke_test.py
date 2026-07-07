import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.literary import normalize_literary_style

print('NTPE TER-v2.0 Smoke Test')
out = normalize_literary_style('留下了鄭泰義一個簡短的回答。突然感覺到幾十年的疲勞一下子都湧上來了。')
assert '留下了鄭泰義' not in out
assert '彷彿積壓了數十年的疲憊，一口氣湧了上來' in out
print('PASS')
