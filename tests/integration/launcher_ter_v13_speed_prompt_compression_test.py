from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package, load_locked_dictionary


def main():
    opt = TxtTranslationOptions(input_path=Path('tests/literary/Smoke_Set/original_ko.txt'), output_dir=Path('tmp'), quality_profile='literary')
    package = build_prompt_package(
        options=opt,
        chunk_text='「일레이!」 정태의는 그를 불렀다.',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=load_locked_dictionary(ROOT),
    )
    checks = [
        ('Prompt v1.3 mode', package['prompt']['prompt_mode'] == 'compact_literary_v4_ter_v1_3'),
        ('Max tokens compact', package['model_profile']['max_output_tokens'] <= 900),
        ('Prompt profiler compact', package['prompt']['prompt_profile']['total_tokens'] < 420),
        ('Dynamic glossary compact', '일레이=伊萊' in package['prompt']['user_prompt']),
    ]
    for name, ok in checks:
        print(f'{name:<34} {"PASS" if ok else "FAIL"}')
        if not ok:
            raise SystemExit(1)
    print('PASS')


if __name__ == '__main__':
    main()
