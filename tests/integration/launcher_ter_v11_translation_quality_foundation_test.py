from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import load_locked_dictionary, build_prompt_package, TxtTranslationOptions


def main():
    locked = load_locked_dictionary(ROOT)
    opt = TxtTranslationOptions(input_path=Path('tests/literary/Smoke_Set/original_ko.txt'), output_dir=Path('tmp'), quality_profile='literary')
    package = build_prompt_package(
        options=opt,
        chunk_text='일레이는 정태의를 바라보았다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    prompt = package['prompt']['user_prompt']
    checks = [
        ('Prompt has compact mode', package['prompt']['prompt_mode'] == 'compact_literary_v3'),
        ('Prompt locks 일레이', '일레이 => 伊萊' in prompt),
        ('Prompt locks 정태의', '정태의 => 鄭泰義' in prompt),
        ('Prompt includes forbidden alias', '伊蕾' in prompt),
        ('Prompt profiler exists', package['prompt']['prompt_profile']['total_tokens'] > 0),
    ]
    for name, ok in checks:
        print(f'{name:<32} {"PASS" if ok else "FAIL"}')
        if not ok:
            raise SystemExit(1)
    print('PASS')

if __name__ == '__main__':
    main()
