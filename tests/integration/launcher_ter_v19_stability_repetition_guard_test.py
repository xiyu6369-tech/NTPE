from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary.literary_style_normalizer import normalize_literary_style


def check(name, condition):
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)

text = '伊萊微微挑了挑眉，轉頭看向鄭泰義。突然感覺到幾十年的疲勞一下子都湧上來了。'
out = normalize_literary_style(text)
check('Gaze Naturalness', '轉頭看了過來' in out)
check('Fatigue Naturalness', '彷彿積壓了數十年的疲憊一口氣湧了上來' in out)
print('PASS')
