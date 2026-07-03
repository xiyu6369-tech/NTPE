"""RC.1 Web UI regression guard."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionRegistry

def test_webui_frozen_component_present():
    registry = RegressionRegistry.default()
    assert registry.require("web_ui").frozen is True
    assert registry.require("web_ui").version == "1.0.0-rc.1"

if __name__ == "__main__":
    test_webui_frozen_component_present(); print("PASS")
