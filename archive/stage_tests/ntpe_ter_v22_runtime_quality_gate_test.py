from pathlib import Path

from core.translation_runtime.runtime_qa import RuntimeQAPolicy, analyze_runtime_quality
from lts.txt_translation_runtime import analyze_translation_quality, TxtTranslationOptions

print('NTPE TER-v2.2 Runtime Quality Gate Test')
print('=' * 44)
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))
    print(f'{name:<32} {"PASS" if condition else "FAIL"}')

source = '정태의는 일라이를 바라보았다. 그는 잠시 침묵했다.'
locked = {'정태의': '鄭泰義', '일라이': '伊萊'}

qa = analyze_runtime_quality(
    source,
    '鄭泰義看著伊萊。他沉默了片刻。',
    RuntimeQAPolicy(min_length_ratio=0.1, max_korean_chars=0),
    locked_dictionary=locked,
    alias_map={'伊蕾': '伊萊'},
    simplified_terms=['这里'],
)
check('Clean Translation Gate', qa['passed'])
check('Metrics Present', qa['metrics']['locked_term_violations'] == 0)

bad = analyze_runtime_quality(
    source,
    '정태의看著伊蕾。这里。太短。',
    RuntimeQAPolicy(min_length_ratio=0.9, max_korean_chars=0, simplified_chinese_policy='fail'),
    locked_dictionary=locked,
    alias_map={'伊蕾': '伊萊'},
    simplified_terms=['这里'],
)
codes = {issue['code'] for issue in bad['issues']}
check('Korean Residue Detected', 'KOREAN_RESIDUE' in codes)
check('Locked Alias Detected', 'LOCKED_TERM_VIOLATION' in codes)
check('Simplified Fail Detected', 'SIMPLIFIED_CHINESE' in codes and not bad['passed'])

repeat = analyze_runtime_quality(
    '그는 기다렸다. 그는 기다렸다. 그는 기다렸다.',
    '他等著。他等著。他等著。',
    RuntimeQAPolicy(min_length_ratio=0.1, max_repeated_sentences=1),
)
check('Repeated Sentence Detected', any(i['code'] == 'REPEATED_SENTENCES' for i in repeat['issues']))

options = TxtTranslationOptions(
    input_path=Path('input.txt'),
    output_dir=Path('output'),
    min_length_ratio=0.1,
    max_korean_chars=0,
    simplified_chinese_policy='fail',
)
runtime_report = analyze_translation_quality(source, '鄭泰義看著伊蕾。这里。', options, locked_dictionary=locked)
runtime_codes = {issue['code'] for issue in runtime_report['issues']}
check('TXT Runtime Uses Gate', 'LOCKED_TERM_VIOLATION' in runtime_codes and 'SIMPLIFIED_CHINESE' in runtime_codes)

if not all(ok for _, ok in checks):
    raise SystemExit(1)
print('PASS')
