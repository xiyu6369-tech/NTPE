import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ntpe_production_translate import _normalize_regression_sets


def main():
    assert _normalize_regression_sets(["golden"]) == ("Test_Set_A",)
    print("PS-04.1 Smoke PASS")
    print("PASS")


if __name__ == "__main__":
    main()
