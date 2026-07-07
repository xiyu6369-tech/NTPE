# =====================================================
# NTPE 1.2 — Translation Engine Refactoring v1.5 Test
# Literary Polish v2
# =====================================================
from core.literary import LiteraryPromptBuilder, normalize_literary_style


def check(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)

chunk = '「일레이!」 정태의는 그를 불렀다. 일레이는 눈썹을 치켜올렸다.'
res = LiteraryPromptBuilder().build(
    chunk_text=chunk,
    locked_dictionary={'일레이': '伊萊', '정태의': '鄭泰義'},
    profile='literary',
)
profile = res.prompt_profile.to_dict()
check('Prompt Mode v1.5', res.to_prompt_dict()['prompt_mode'] == 'compact_literary_v6_ter_v1_5')
check('Prompt Still Compact', profile['total_tokens'] < 430)
check('Glossary Locked', '일레이=伊萊' in res.user_prompt and '정태의=鄭泰義' in res.user_prompt)

sample = '伊萊笑著回答道：「當然。」說完便轉身離去，只留下了一句模糊的話。伊萊抬了抬眉毛。事情已經變得最壞了。'
cleaned = normalize_literary_style(sample)
check('Polish Ambiguous Reply', '只留下了一句模糊的話' not in cleaned and '怎麼解讀都說得通' in cleaned)
check('Polish Eyebrow', '抬了抬眉毛' not in cleaned and '挑了挑眉' in cleaned)
check('Polish Worst Situation', '糟到不能再糟' in cleaned)
print('PASS')
