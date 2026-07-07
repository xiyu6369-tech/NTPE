from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.literary import normalize_literary_style


def main():
    sample = '事情已經變得最壞了。伊萊抬了抬眉毛。'
    cleaned = normalize_literary_style(sample)
    ok = '糟到不能再糟' in cleaned and '挑了挑眉' in cleaned
    print(f'TER v1.5 style smoke       {"PASS" if ok else "FAIL"}')
    if not ok:
        raise SystemExit(1)
    print('PASS')


if __name__ == '__main__':
    main()
