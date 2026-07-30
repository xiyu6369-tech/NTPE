from core.literary import normalize_literary_style

print('NTPE TER-v1.7 Narrative Naturalness Test')
print('========================================')

checks = []

def check(name, condition):
    checks.append((name, bool(condition)))
    print(f'{name:<34} {"PASS" if condition else "FAIL"}')

sample = '鄭泰義叫住了想要轉身離開的伊萊，伊萊挑了挑眉，轉頭看向鄭泰義。鄭泰義心情沉重地瞪了伊萊一會兒。'
out = normalize_literary_style(sample)
check('About To Leave', '正要轉身離去' in out and '想要轉身' not in out)
check('Gaze Naturalness', '轉頭看了過來' in out and '看向鄭泰義' not in out)
check('Pronoun Focus', '神情沉重地瞪著他看了一會兒' in out)

fatigue = '突然之間，幾十年的疲勞感覺像洪水一樣湧了上來。'
fatigue_out = normalize_literary_style(fatigue)
check('Fatigue Metaphor', '彷彿積壓了數十年的疲憊一口氣湧了上來' in fatigue_out)

if not all(ok for _, ok in checks):
    raise SystemExit(1)
print('PASS')
