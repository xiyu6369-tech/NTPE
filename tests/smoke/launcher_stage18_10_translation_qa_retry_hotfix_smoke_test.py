import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from lts.txt_translation_runtime import TxtTranslationOptions, analyze_translation_quality


def main() -> int:
    options = TxtTranslationOptions(input_path=Path('input.txt'), output_dir=Path('output'))
    qa = analyze_translation_quality('정태의', '鄭泰義', options)
    if not qa.get('passed'):
        raise SystemExit('simple zh-TW output should pass QA')
    print('Stage-18.10 Smoke')
    print('Translation QA       PASS')
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())