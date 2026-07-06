import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import apply_locked_dictionary


def main():
    assert apply_locked_dictionary("定泰義", {"정태의": "鄭泰義"}) == "鄭泰義"
    print("PASS")


if __name__ == "__main__":
    main()
