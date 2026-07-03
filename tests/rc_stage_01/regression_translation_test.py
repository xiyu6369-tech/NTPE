"""RC.1 translation regression guard."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionRunner

def test_translation_regression_baseline():
    result = RegressionRunner(ROOT).run()
    categories = {item["category"] for item in result["suite"]["results"]}
    assert "translation" in categories
    assert "workflow" in categories
    assert "runtime" in categories
    assert "external_api" in categories
    assert "web_ui" in categories
    assert result["passed"] is True

if __name__ == "__main__":
    test_translation_regression_baseline(); print("PASS")
