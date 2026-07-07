from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import apply_locked_dictionary


def main():
    text = apply_locked_dictionary('伊蕾看著정태의。', {'일레이': '伊萊', '정태의': '鄭泰義'})
    ok = text == '伊萊看著鄭泰義。'
    print(f'TER-v1.1 name lock smoke       {"PASS" if ok else "FAIL"}')
    if not ok:
        raise SystemExit(1)
    print('PASS')

if __name__ == '__main__':
    main()
