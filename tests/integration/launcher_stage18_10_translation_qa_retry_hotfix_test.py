import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from lts.txt_translation_runtime import TxtTranslationOptions, analyze_translation_quality, build_qa_retry_user_prompt


def main() -> int:
    options = TxtTranslationOptions(input_path=Path('input.txt'), output_dir=Path('output'))
    qa = analyze_translation_quality('원문입니다.', '원문입니다.' * 40, options)
    if qa.get('passed'):
        raise SystemExit('QA should reject Korean residue')
    prompt = build_qa_retry_user_prompt('Translate this:\n원문입니다.', qa, 2)
    if 'KOREAN_RESIDUE' not in prompt or '台灣繁體中文' not in prompt:
        raise SystemExit('retry prompt missing QA guidance')
    print('Stage-18.10 Integration')
    print('QA Retry Prompt      PASS')
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())