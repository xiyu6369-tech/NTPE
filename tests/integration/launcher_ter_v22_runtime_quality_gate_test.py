from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions, analyze_translation_quality

print('NTPE TER-v2.2 Runtime Quality Gate Integration Test')
print('=' * 56)

options = TxtTranslationOptions(
    input_path=Path('input.txt'),
    output_dir=Path('output'),
    min_length_ratio=0.1,
    max_korean_chars=0,
    simplified_chinese_policy='fail',
)
source = '정태의는 일라이를 보았다.'
locked = {'정태의': '鄭泰義', '일라이': '伊萊'}
report = analyze_translation_quality(source, '鄭泰義看著伊蕾。这里。', options, locked_dictionary=locked)
codes = {issue['code'] for issue in report['issues']}
assert 'LOCKED_TERM_VIOLATION' in codes
assert 'SIMPLIFIED_CHINESE' in codes
assert report['metrics']['locked_term_violations'] >= 1
assert report['metrics']['simplified_hits'] >= 1
print('Runtime Quality Gate       PASS')
print('TXT Runtime Bridge         PASS')
print('PASS')
