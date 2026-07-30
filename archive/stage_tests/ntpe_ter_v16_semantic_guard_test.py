from core.literary import normalize_literary_style

print('NTPE TER-v1.6 Semantic Guard Test')
print('==================================')

checks = []

def check(name, condition):
    checks.append((name, bool(condition)))
    print(f'{name:<34} {"PASS" if condition else "FAIL"}')

sample_reply = '伊萊輕笑著說：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。'
cleaned_reply = normalize_literary_style(sample_reply)
check('Ambiguous Reply Guard', '留下了鄭泰義一個' not in cleaned_reply and '只答了一句「當然」' in cleaned_reply)

sample_repeat = '鄭泰義就站在那裡，直到伊萊轉過彎角，完全消失在視線中為止。等伊萊徹底消失在視線裡，鄭泰義就靠在牆上，滑坐在地上。'
cleaned_repeat = normalize_literary_style(sample_repeat)
check('Disappearance Dedupe', cleaned_repeat.count('消失在視線') == 1 and '才靠在牆上' in cleaned_repeat)

sample_style = '伊萊抬了抬眉毛。事情已經變得最壞了。'
cleaned_style = normalize_literary_style(sample_style)
check('Existing Polish Retained', '挑了挑眉' in cleaned_style and '糟到不能再糟' in cleaned_style)

if not all(ok for _, ok in checks):
    raise SystemExit(1)
print('PASS')
