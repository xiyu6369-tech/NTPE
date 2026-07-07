from pathlib import Path

from lts.txt_translation_runtime import (
    apply_locked_dictionary,
    build_translation_alias_map,
    load_locked_dictionary,
    build_prompt_package,
    TxtTranslationOptions,
    analyze_translation_quality,
)


def check(name, condition):
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    root = Path(__file__).resolve().parent
    locked = load_locked_dictionary(root)
    check('일레이 locked', locked.get('일레이') == '伊萊')
    aliases = build_translation_alias_map({'일레이': '伊萊'})
    check('伊蕾 alias exists', aliases.get('伊蕾') == '伊萊')
    fixed = apply_locked_dictionary('伊蕾回頭看著정태의。', {'일레이': '伊萊', '정태의': '鄭泰義'})
    check('Alias normalized', '伊萊' in fixed and '伊蕾' not in fixed)
    check('Source residue normalized', '鄭泰義' in fixed and '정태의' not in fixed)

    opt = TxtTranslationOptions(input_path=Path('Smoke_Set/original_ko.txt'), output_dir=Path('output'), quality_profile='literary')
    pkg = build_prompt_package(
        options=opt,
        chunk_text='「일레이!」 정태의는 그를 불렀다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    prompt = pkg['prompt']['user_prompt']
    check('Dynamic glossary includes 일레이', '일레이 => 伊萊' in prompt)
    check('Forbidden alias includes 伊蕾', '伊蕾' in prompt and '伊萊' in prompt)

    qa = analyze_translation_quality('일레이가 말했다.', '伊蕾說道。', opt, locked_dictionary={'일레이': '伊萊'})
    check('QA catches locked alias', not qa['passed'])
    qa2 = analyze_translation_quality('일레이가 말했다.', '伊萊說道。', opt, locked_dictionary={'일레이': '伊萊'})
    check('QA passes correct lock', qa2['passed'])
    print('PASS')


if __name__ == '__main__':
    main()
