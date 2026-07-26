import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ntpe_production_translate import _normalize_regression_sets


def main():
    assert _normalize_regression_sets(["golden"]) == ("Golden_Set",)
    assert _normalize_regression_sets(["Test_Set_A", "Test_Set_0"]) == (
        "Golden_Set",
        "Smoke_Set",
    )
    print("PS-04.1 Smoke PASS")
    print("PASS")


if __name__ == "__main__":
    main()
