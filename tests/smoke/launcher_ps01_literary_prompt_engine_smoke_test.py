# =====================================================
# NTPE PS-01 Smoke Test
# =====================================================
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    build_prompt_package,
)


def main() -> int:
    required = [
        ROOT / 'tests' / 'literary' / 'README.md',
        ROOT / 'tests' / 'literary' / 'Smoke_Set' / 'original_ko.txt',
        ROOT / 'tests' / 'literary' / 'Golden_Set' / 'reference_notes.md',
        ROOT / 'tests' / 'literary' / 'Regression_Set' / 'evaluation.md',
        ROOT / 'tests' / 'literary' / 'outputs' / 'PS-01' / 'README.md',
    ]
    for path in required:
        ok = path.exists()
        print(f'{path.relative_to(ROOT)} {"PASS" if ok else "FAIL"}')
        if not ok:
            return 1
    options = TxtTranslationOptions(
        input_path=ROOT / 'tests' / 'literary' / 'Smoke_Set' / 'original_ko.txt',
        output_dir=ROOT / 'work' / 'ps01_smoke',
        quality_profile='literary',
    )
    package = build_prompt_package(
        options=options,
        chunk_text='일레이는 정태의를 바라보았다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={'일레이': '伊萊', '정태의': '鄭泰義'},
    )
    prompt = package['prompt']['user_prompt']
    checks = [
        ('compact literary mode', package['prompt']['prompt_mode'] == 'compact_literary_v6_ter_v1_5'),
        ('locked name map', package['knowledge']['locked_dictionary'] == {
            '일레이': '伊萊', '정태의': '鄭泰義',
        }),
        ('locked names in prompt', '일레이=伊萊' in prompt and '정태의=鄭泰義' in prompt),
        ('prompt profiler', package['prompt']['prompt_profile']['total_tokens'] > 0),
    ]
    for name, ok in checks:
        print(f'{name:<24} {"PASS" if ok else "FAIL"}')
        if not ok:
            return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
