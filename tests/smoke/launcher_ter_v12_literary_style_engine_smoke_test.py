from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, format_translation_output


def main():
    opt = TxtTranslationOptions(input_path=Path('x.txt'), output_dir=Path('output'))
    text = format_translation_output('伊萊則是稍微扬起眉毛。', opt)
    ok = '微微挑了挑眉' in text and '扬' not in text
    print(f'TER-v1.2 literary style smoke   {"PASS" if ok else "FAIL"}')
    if not ok:
        raise SystemExit(1)
    print('PASS')

if __name__ == '__main__':
    main()
