# =====================================================
# NTPE PS-01 Smoke Test
# =====================================================
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    required = [
        ROOT / 'tests' / 'literary' / 'README.md',
        ROOT / 'tests' / 'literary' / 'Test_Set_0' / 'original_ko.txt',
        ROOT / 'tests' / 'literary' / 'Test_Set_A' / 'reference_notes.md',
        ROOT / 'tests' / 'literary' / 'Test_Set_B' / 'evaluation.md',
        ROOT / 'tests' / 'literary' / 'outputs' / 'PS-01' / 'README.md',
    ]
    for path in required:
        ok = path.exists()
        print(f'{path.relative_to(ROOT)} {"PASS" if ok else "FAIL"}')
        if not ok:
            return 1
    prompt_runtime = (ROOT / 'lts' / 'txt_translation_runtime.py').read_text(encoding='utf-8')
    checks = [
        ('literary_translate_txt', 'literary_translate_txt' in prompt_runtime),
        ('literary policy', '不要強行套用特定地區用語' in prompt_runtime),
        ('PS metadata', '1.2-ps-01-literary-prompt-engine' in prompt_runtime),
    ]
    for name, ok in checks:
        print(f'{name:<24} {"PASS" if ok else "FAIL"}')
        if not ok:
            return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
