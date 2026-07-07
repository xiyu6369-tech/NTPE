from pathlib import Path
import os

from core.literary import normalize_literary_style
from core.translation_engine.nvidia_client import NvidiaClient
from lts.txt_translation_runtime import detect_quality_lock_violations, _effective_provider_timeout

print('NTPE TER-v2.0 Quality Lock Baseline Test')
print('========================================')

checks = []

def check(name, condition):
    checks.append((name, bool(condition)))
    print(f'{name:<36} {"PASS" if condition else "FAIL"}')

bad_reply = '伊萊輕笑著說：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。'
fixed_reply = normalize_literary_style(bad_reply)
check('Wrong Reply Object Fixed', '留下了鄭泰義' not in fixed_reply and '簡短而曖昧的回答' in fixed_reply)

bad_repeat = '鄭泰義就站在原地，直到伊萊轉過彎角，徹底消失在視線裡。等伊萊完全消失後，鄭泰義就靠在牆上，滑坐在地上。'
fixed_repeat = normalize_literary_style(bad_repeat)
check('Near Duplicate Removed', fixed_repeat.count('消失在視線') == 1 and ('才靠著牆' in fixed_repeat or '才靠在牆上' in fixed_repeat))

bad_fatigue = '突然感覺到幾十年的疲勞一下子都湧上來了。'
fixed_fatigue = normalize_literary_style(bad_fatigue)
check('Fatigue Baseline Fixed', '彷彿積壓了數十年的疲憊，一口氣湧了上來' in fixed_fatigue)

violations = detect_quality_lock_violations(bad_reply + bad_repeat + bad_fatigue)
check('Quality Lock Detects Issues', len(violations) >= 3)

os.environ['NTPE_API_TIMEOUT'] = '180'
os.environ['NTPE_CURRENT_API_TIMEOUT'] = '90'
client = NvidiaClient(api_key='nvapi-test')
check('Current Timeout Honored', client.timeout == 90)
os.environ.pop('NTPE_CURRENT_API_TIMEOUT', None)

package = {'source': {'char_count': 455}}
os.environ['NTPE_API_TIMEOUT'] = '180'
os.environ.pop('NTPE_SHORT_CHUNK_FIRST_TIMEOUT', None)
check('Short Timeout Default', _effective_provider_timeout(package, 1) == 90)

if not all(ok for _, ok in checks):
    raise SystemExit(1)
print('PASS')
