from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package, load_locked_dictionary, get_max_output_tokens, format_translation_output


def check(name, condition):
    print(f"{name:<42} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    root = Path(__file__).resolve().parent
    opt = TxtTranslationOptions(
        input_path=Path('tests/literary/Smoke_Set/original_ko.txt'),
        output_dir=Path('output'),
        quality_profile='literary',
    )
    locked = load_locked_dictionary(root)
    chunk = '「일레이!」 정태의는 그를 불렀다. 일레이가 눈썹을 치켜올렸다.'
    pkg = build_prompt_package(
        options=opt,
        chunk_text=chunk,
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    prompt = pkg['prompt']['user_prompt']
    profile = pkg['prompt']['prompt_profile']
    check('Prompt mode v1.3', pkg['prompt']['prompt_mode'] == 'compact_literary_v4_ter_v1_3')
    check('Compact glossary format', '일레이=伊萊' in prompt and '일레이 =>' not in prompt)
    check('Prompt compressed', profile['total_tokens'] < 420)
    check('Literary max tokens compressed', get_max_output_tokens(chunk, opt) <= 900)
    formatted = format_translation_output('伊萊則是用沉重的心情看他，然後就轉身走了，全數湧了上來了。', opt)
    check('Style cleanup v1.3', '心情沉重地' in formatted and '說完便轉身離去' in formatted and '全數湧了上來了' not in formatted)
    print('PASS')


if __name__ == '__main__':
    main()
