# =====================================================
# NTPE 1.2 Production Stabilization — PS-03 Test
# Translation Corpus Evaluation Engine
# =====================================================
from pathlib import Path

from ntpe_literary_evaluation import evaluate_stage_outputs, evaluate_translation_text

root = Path(__file__).resolve().parent
stage_dir = root / "tests" / "literary" / "outputs" / "PS-03-test" / "Test_Set_0"
stage_dir.mkdir(parents=True, exist_ok=True)
(stage_dir / "original_ko_zh.txt").write_text(
    "鄭泰義一時說不出話來。凱爾若無其事地望著窗外。\n「沒關係。反正事情都已經發生了。」\n",
    encoding="utf-8",
)
source = (root / "tests" / "literary" / "Test_Set_0" / "original_ko.txt").read_text(encoding="utf-8")
result = evaluate_translation_text(source, (stage_dir / "original_ko_zh.txt").read_text(encoding="utf-8"))
assert result["overall_score"] >= 80, result
assert result["status"] == "success", result
report = evaluate_stage_outputs(root, "PS-03-test")
assert report["summary"]["existing_outputs"] >= 1
assert Path(report["report_md"]).exists()
assert Path(report["report_json"]).exists()
assert Path(report["diff_md"]).exists()
print("PASS")
