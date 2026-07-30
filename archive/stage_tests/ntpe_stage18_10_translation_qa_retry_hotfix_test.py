# =====================================================
# NTPE 1.2 Professional — Stage-18.10 Translation QA Retry Hotfix Test
# =====================================================
from pathlib import Path

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    build_qa_retry_user_prompt,
)


def main() -> int:
    options = TxtTranslationOptions(input_path=Path('input.txt'), output_dir=Path('output'))
    qa = analyze_translation_quality('정태의는 문을 열었다.', '정태의는 문을 열었다.' * 30, options)
    assert qa['passed'] is False
    assert qa['issues'][0]['code'] == 'KOREAN_RESIDUE'
    retry_prompt = build_qa_retry_user_prompt('【待翻譯內容】\n정태의는 문을 열었다.', qa, 2)
    assert 'NTPE 自動重試指令' in retry_prompt
    assert '嚴禁複製韓文原文' in retry_prompt
    assert 'KOREAN_RESIDUE' in retry_prompt
    print('Stage-18.10 Translation QA Retry Hotfix Test')
    print('QA Detection        PASS')
    print('Retry Prompt        PASS')
    print('Bilingual Error     PASS')
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
