from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.literary import LiteraryPromptBuilder, normalize_literary_style


def main():
    builder = LiteraryPromptBuilder()
    result = builder.build(
        chunk_text='「일레이!」 정태의는 일레이를 불렀다.',
        locked_dictionary={'일레이': '伊萊', '정태의': '鄭泰義'},
        profile='literary',
    )
    cleaned = normalize_literary_style('伊萊抬了抬眉毛，只留下了一句模糊的話。')
    checks = [
        ('TER v1.5 prompt mode', result.to_prompt_dict()['prompt_mode'] == 'compact_literary_v6_ter_v1_5'),
        ('TER v1.5 compact', result.prompt_profile.total_tokens < 430),
        ('TER v1.5 polish', '抬了抬眉毛' not in cleaned and '模糊的話' not in cleaned),
    ]
    for name, ok in checks:
        print(f'{name:<32} {"PASS" if ok else "FAIL"}')
        if not ok:
            raise SystemExit(1)
    print('PASS')


if __name__ == '__main__':
    main()
