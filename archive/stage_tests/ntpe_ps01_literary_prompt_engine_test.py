# =====================================================
# NTPE 1.2 Production Stabilization — PS-01
# Literary Prompt Engine Test
# =====================================================
from pathlib import Path
import tempfile

from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package, get_max_output_tokens


def main() -> int:
    sample = '정태의는 난감해했다. 카일은 조용히 말했다. "이미 벌어진 일이야."'
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        input_path = root / 'sample.txt'
        input_path.write_text(sample, encoding='utf-8')
        options = TxtTranslationOptions(input_path=input_path, output_dir=root / 'out', quality_profile='literary')
        package = build_prompt_package(
            options=options,
            chunk_text=sample,
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={'정태의': '鄭泰義', '카일': '凱爾'},
            previous_context='',
        )
    system_prompt = package['prompt']['system_prompt']
    user_prompt = package['prompt']['user_prompt']
    checks = [
        ('Literary Mode', package['prompt']['prompt_mode'] == 'literary_translate_txt'),
        ('No Forced Taiwan Wording', '不要強行套用特定地區用語' in user_prompt),
        ('Natural Traditional Chinese', '自然流暢的繁體中文' in system_prompt),
        ('Name Lock Taeui', '정태의 → 鄭泰義' in user_prompt),
        ('Name Lock Kyle', '카일 → 凱爾' in user_prompt),
        ('Subject Accuracy Rule', '主詞' in user_prompt),
        ('Metadata Version', package['metadata']['package_version'] == '1.2-ps-01-literary-prompt-engine'),
        ('Profile Tokens', get_max_output_tokens(sample, options) >= 1200),
    ]
    for name, ok in checks:
        print(f'{name:<28} {"PASS" if ok else "FAIL"}')
        if not ok:
            return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
