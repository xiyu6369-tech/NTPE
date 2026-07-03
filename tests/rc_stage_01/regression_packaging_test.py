"""RC.1 packaging regression guard."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionRegistry

def test_packaging_release_components_present():
    registry = RegressionRegistry.default()
    assert registry.require("packaging").frozen is True
    assert registry.require("release").frozen is True
    assert registry.validate()["valid"] is True

if __name__ == "__main__":
    test_packaging_release_components_present(); print("PASS")
