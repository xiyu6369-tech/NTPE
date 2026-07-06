from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
out = root / "tests" / "literary" / "outputs" / "PS-03-integration" / "Test_Set_0"
out.mkdir(parents=True, exist_ok=True)
(out / "original_ko_zh.txt").write_text(
    "鄭泰義一時說不出話來。凱爾望著窗外。\n「沒關係。反正事情都已經發生了。」\n",
    encoding="utf-8",
)
result = subprocess.run(
    [sys.executable, "launcher_translate.py", "evaluate", "--stage", "PS-03-integration"],
    cwd=root,
    text=True,
    capture_output=True,
)
assert result.returncode == 0, result.stdout + result.stderr
assert "NTPE Literary Evaluation" in result.stdout
assert "overall_score" in result.stdout
print("PASS")
