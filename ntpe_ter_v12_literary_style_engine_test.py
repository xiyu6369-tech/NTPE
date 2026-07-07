from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions, format_translation_output, normalize_taiwan_traditional, build_prompt_package, load_locked_dictionary
from core.literary import normalize_literary_style


def check(name, condition):
    print(f"{name:<40} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    root = Path(__file__).resolve().parent
    opt = TxtTranslationOptions(input_path=Path('tests/literary/Smoke_Set/original_ko.txt'), output_dir=Path('output'), quality_profile='literary')

    sample = '伊萊則是稍微扬起眉毛，然後就轉身走開了。'
    formatted = format_translation_output(sample, opt)
    check('Simplified 扬 normalized', '扬' not in formatted and '揚' not in formatted)
    check('Eyebrow style normalized', '微微挑了挑眉' in formatted)
    check('Leave phrasing normalized', '轉身離去' in formatted)

    idiom = normalize_literary_style('我絕對不會保持沉默。')
    check('Idiom style normalized', '坐視不管' in idiom)

    locked = load_locked_dictionary(root)
    pkg = build_prompt_package(
        options=opt,
        chunk_text='일레이가 눈썹을 치켜올렸다. 정태의는 그를 불렀다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    prompt = pkg['prompt']['user_prompt']
    check('Prompt mode v1.2', pkg['prompt']['prompt_mode'] == 'compact_literary_v3_ter_v1_2')
    check('Prompt asks novel prose', '中文小說正文' in prompt)
    print('PASS')


if __name__ == '__main__':
    main()
