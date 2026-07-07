from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, get_max_output_tokens, format_translation_output


def main():
    opt = TxtTranslationOptions(input_path=Path('x.txt'), output_dir=Path('output'), quality_profile='literary')
    ok = get_max_output_tokens('일레이가 말했다.' * 10, opt) <= 900
    text = format_translation_output('그는挑了挑眉毛，然後就轉身走了。', opt)
    ok = ok and '挑了挑眉' in text and '說完便轉身離去' in text
    print(f'TER-v1.3 speed prompt smoke       {"PASS" if ok else "FAIL"}')
    if not ok:
        raise SystemExit(1)
    print('PASS')


if __name__ == '__main__':
    main()
