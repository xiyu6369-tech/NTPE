from pathlib import Path

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    apply_locked_dictionary,
    build_prompt_package,
    load_locked_dictionary,
    analyze_translation_quality,
    get_max_output_tokens,
)


def check(label, condition):
    print(f"{label:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    root = Path(__file__).resolve().parent
    locked = load_locked_dictionary(root)
    opt = TxtTranslationOptions(input_path=Path('input/sample.txt'), output_dir=Path('output'), quality_profile='novel')
    package = build_prompt_package(
        options=opt,
        chunk_text='정태의는 조용히 일라이를 바라보았다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
        previous_context='鄭泰義剛才停下腳步。',
    )
    fixed = apply_locked_dictionary('定泰義看著정태의。', locked)
    qa = analyze_translation_quality('정태의', fixed, opt, package['knowledge']['locked_dictionary'])
    check('Character override extraction', locked.get('정태의') == '鄭泰義')
    check('Name lock correction', fixed.count('鄭泰義') == 2 and '定泰義' not in fixed and '정태의' not in fixed)
    check('Prompt includes novel quality', '出版小說' in package['prompt']['system_prompt'] or '出版級' in package['prompt']['system_prompt'])
    check('Prompt includes previous context', '前文參考' in package['prompt']['user_prompt'])
    check('Locked term QA passes after fix', qa['passed'])
    check('Novel max output token profile', 1000 <= get_max_output_tokens('가' * 1000, opt) <= 3200)
    print('PASS')


if __name__ == '__main__':
    main()
