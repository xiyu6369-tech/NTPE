"""RC.1 REST regression guard."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionRegistry

def test_rest_api_frozen_component_present():
    registry = RegressionRegistry.default()
    assert registry.require("external_api").frozen is True
    assert registry.validate()["frozen_api_safe"] is True

if __name__ == "__main__":
    test_rest_api_frozen_component_present(); print("PASS")
