from pathlib import Path

from core.literary import LiteraryPromptBuilder
from ntpe_production_translate import _normalize_regression_sets
from ntpe_literary_regression import discover_test_sets, ensure_literary_structure

root = Path.cwd()
ensure_literary_structure(root)

assert _normalize_regression_sets(None) == ("Smoke_Set", "Golden_Set", "Regression_Set")
assert _normalize_regression_sets(["Test_Set_A", "smoke"]) == ("Golden_Set", "Smoke_Set")
sets = discover_test_sets(root)
assert {item["name"] for item in sets} == {"Smoke_Set", "Golden_Set", "Regression_Set"}

text = "정태의는 난감해하고 있었다. 카일이 그렇게 주장하며 정태의를 데리고 섬으로 왔다."
result = LiteraryPromptBuilder().build(
    chunk_text=text,
    locked_dictionary={"정태의": "鄭泰義", "카일": "凱爾", "일라이": "伊萊"},
    alias_map={"定泰義": "鄭泰義", "正太義": "鄭泰義"},
    previous_context="凱爾帶鄭泰義來到南國島嶼度假。",
    profile="literary",
)
assert result.profile == "literary"
assert result.prompt_profile.total_tokens < 900
assert "정태의 => 鄭泰義" in result.user_prompt
assert "카일 => 凱爾" in result.user_prompt
assert "일라이" not in result.user_prompt
assert "凱爾" in result.user_prompt and "主體" in result.user_prompt
assert result.to_prompt_dict()["prompt_mode"] == "compact_literary_v3"
print("PASS")
