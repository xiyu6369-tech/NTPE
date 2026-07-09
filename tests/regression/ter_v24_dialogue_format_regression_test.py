from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import format_translation_output


def test_curly_dialogue_quotes_are_converted_to_corner_brackets() -> None:
    text = '“……但現在擔心也無濟於事。”'
    assert format_translation_output(text) == '「……但現在擔心也無濟於事。」'
