"""RC.1 runtime regression guard."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionRegistry

def test_runtime_api_frozen_component_present():
    registry = RegressionRegistry.default()
    assert registry.require("runtime_api").frozen is True
    assert registry.require("workflow").status == "PASS"
    assert registry.require("platform_services").status == "PASS"

if __name__ == "__main__":
    test_runtime_api_frozen_component_present(); print("PASS")
