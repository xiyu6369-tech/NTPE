from core.literary.literary_style_normalizer import normalize_literary_style
from lts.txt_translation_runtime import _provider_model_chain, _provider_model_for_attempt


def check(name, condition):
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)

sample = '伊萊輕笑著說：「當然。」說完便轉身離去，只留下了一句模稜兩可的話。'
out = normalize_literary_style(sample)
check('Ambiguous Reply Stable', '簡短的回答' in out and '模稜兩可的話' not in out)

repeat = '鄭泰義就站在原地，直到伊萊轉過彎角，徹底消失在視線裡。等伊萊完全消失後，鄭泰義就靠在牆上，滑坐在地上。'
repeat_out = normalize_literary_style(repeat)
check('Disappearance Repetition Guard', repeat_out.count('消失') == 1 and '才靠在牆上' in repeat_out)

fatigue = '突然感覺到幾十年的疲勞一下子都湧上來了。'
fatigue_out = normalize_literary_style(fatigue)
check('Fatigue Stability', '彷彿積壓了數十年的疲憊一口氣湧了上來' in fatigue_out)

check('Model Chain Primary', _provider_model_chain('model-a')[0] == 'model-a')
check('Model Attempt Primary', _provider_model_for_attempt({'model_profile': {'model': 'model-a'}}, 1) == 'model-a')
print('PASS')
