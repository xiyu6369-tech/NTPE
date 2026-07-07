from core.literary import normalize_literary_style
from core.translation_engine.translation_engine import TranslationEngine

print('NTPE TER-v1.8 Character Tone + API Stability Test')
print('==================================================')

checks = []
def check(name, condition):
    checks.append((name, bool(condition)))
    print(f'{name:<34} {"PASS" if condition else "FAIL"}')

text = '伊萊開心地笑了，說：「當然。」說完便轉身離去，只留下那句令人費解的話。'
out = normalize_literary_style(text)
check('Ilay Tone Guard', '開心地笑' not in out and '覺得有趣' in out)
check('Ambiguous Reply', '只答了一句「當然」' in out or '怎麼解讀' in out)

engine = TranslationEngine(root='.')
package = {'source': {'char_count': 455}, 'runtime': {'provider_attempt': 1}}
import os
os.environ['NTPE_API_TIMEOUT'] = '180'
check('Short First Timeout Cap', engine._get_timeout(package) <= 120)
package['runtime']['provider_attempt'] = 2
check('Retry Uses Full Timeout', engine._get_timeout(package) == 180)

if not all(ok for _, ok in checks):
    raise SystemExit(1)
print('PASS')
