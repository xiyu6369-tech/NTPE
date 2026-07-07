import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary import LiteraryPromptBuilder, normalize_profile


def test_profile_aliases():
    assert normalize_profile("novel") == "literary"
    assert normalize_profile("quality") == "premium"


def test_builder_includes_context():
    r = LiteraryPromptBuilder().build(
        chunk_text="정태의는 난감해하고 있었다. 카일이 주장했다.",
        locked_dictionary={"정태의": "鄭泰義", "카일": "凱爾"},
        profile="literary",
    )
    assert "Narrative" in r.user_prompt
    assert "Character" in r.user_prompt
    assert "鄭泰義" in r.user_prompt
    assert "凱爾" in r.user_prompt
