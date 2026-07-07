# =====================================================
# NTPE 1.2 — Translation Engine Refactoring v1.4 Test
# Speed + Semantic Accuracy
# =====================================================
from core.literary import LiteraryPromptBuilder, normalize_literary_style
from lts.txt_translation_runtime import TxtTranslationOptions, get_max_output_tokens
from pathlib import Path


def check(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)


chunk = '「일레이!」\n정태의는 그를 불렀다. 일레이는 눈썹을 치켜올렸다.'
res = LiteraryPromptBuilder().build(
    chunk_text=chunk,
    locked_dictionary={'일레이': '伊萊', '정태의': '鄭泰義'},
    profile='literary',
)
profile = res.prompt_profile.to_dict()
check('Prompt Compact', profile['total_tokens'] < 520)
check('Glossary Matched', '일레이=伊萊' in res.user_prompt and '정태의=鄭泰義' in res.user_prompt)
check('Output Contract', '禁止標題' in res.user_prompt)

options = TxtTranslationOptions(input_path=Path('dummy.txt'), output_dir=Path('output'), quality_profile='literary')
check('Short Max Tokens', get_max_output_tokens('가' * 455, options) <= 560)
check('Medium Max Tokens', get_max_output_tokens('가' * 1000, options) <= 1200)

sample = '伊萊開心地笑了，說：「當然。」說完便轉身離去，留下了這句話。事情已經變得最糟糕了。'
cleaned = normalize_literary_style(sample)
check('Ambiguous Reply Cleanup', '留下了這句話' not in cleaned)
check('Semantic Cleanup', '最糟的方向' in cleaned)
print('PASS')
