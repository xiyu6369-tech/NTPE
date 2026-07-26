from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ntpe_literary_regression import (
    LiteraryRegressionOptions,
    discover_test_sets,
    normalize_test_set_name,
    run_literary_regression,
)

LITERARY_ROOT = ROOT / "tests" / "literary"
CANONICAL_SETS = ("Smoke_Set", "Golden_Set", "Regression_Set")
LEGACY_ALIASES = {
    "Test_Set_0": "Smoke_Set",
    "Test_Set_A": "Golden_Set",
    "Test_Set_B": "Regression_Set",
}

result = subprocess.run(
    [sys.executable, "launcher_translate.py", "corpus", "list"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    timeout=30,
)
assert result.returncode == 0, result.stdout + result.stderr
rows = [
    line.split()[0]
    for line in result.stdout.splitlines()
    if " READY " in f" {line} "
]
assert rows == list(CANONICAL_SETS)
assert not any(name in result.stdout for name in LEGACY_ALIASES)

listed = discover_test_sets(ROOT)
assert tuple(item["name"] for item in listed) == CANONICAL_SETS
assert all(item["exists"] and item["has_content"] for item in listed)
assert all(Path(item["path"]).is_dir() for item in listed)
committed_source_sets = {
    directory.name
    for directory in LITERARY_ROOT.iterdir()
    if directory.is_dir() and (directory / "original_ko.txt").is_file()
}
assert committed_source_sets == set(CANONICAL_SETS)

for legacy, canonical in LEGACY_ALIASES.items():
    assert normalize_test_set_name(legacy) == canonical
    resolved = discover_test_sets(ROOT, (legacy,))
    assert len(resolved) == 1
    assert resolved[0]["name"] == canonical
    assert resolved[0]["exists"] and resolved[0]["has_content"]
    assert Path(resolved[0]["source"]) == LITERARY_ROOT / canonical / "original_ko.txt"

with TemporaryDirectory() as directory:
    temporary_root = Path(directory)
    temporary_literary = temporary_root / "tests" / "literary"
    temporary_literary.mkdir(parents=True)
    for name in CANONICAL_SETS:
        shutil.copytree(LITERARY_ROOT / name, temporary_literary / name)
    with patch(
        "core.translation_engine.nvidia_client.requests.post",
        side_effect=AssertionError("Provider/network call forbidden"),
    ):
        report = run_literary_regression(
            LiteraryRegressionOptions(
                root=temporary_root,
                test_sets=CANONICAL_SETS,
                stage_name="PS-02-inventory-closure",
                dry_run=True,
                overwrite=True,
                evaluate=False,
            )
        )
    assert report["status"] == "success"
    assert report["summary"]["total"] == 3
    assert report["summary"]["success"] == 3
    assert report["summary"]["skipped"] == 0
    assert report["summary"]["failed"] == 0
    assert report["summary"]["dry_run"] is True
    assert tuple(item["name"] for item in report["records"]) == CANONICAL_SETS
    assert all(item["status"] == "success" for item in report["records"])

print("PASS")


def test_ps02_inventory_closure() -> None:
    assert rows == list(CANONICAL_SETS)
    assert report["summary"]["success"] == 3
    assert report["summary"]["failed"] == 0
