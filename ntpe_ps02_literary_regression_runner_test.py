# =====================================================
# NTPE 1.2 Production Stabilization — PS-02 Test
# =====================================================
from pathlib import Path
from ntpe_literary_regression import LiteraryRegressionOptions, discover_test_sets, ensure_literary_structure, run_literary_regression

root = Path(__file__).resolve().parent
init = ensure_literary_structure(root)
assert init["status"] == "success"
sets = discover_test_sets(root)
assert {item["name"] for item in sets} == {"Test_Set_0", "Test_Set_A", "Test_Set_B"}
report = run_literary_regression(LiteraryRegressionOptions(root=root, test_sets=("Test_Set_0",), stage_name="PS-02-test", dry_run=True, overwrite=True))
assert report["status"] == "success"
assert report["summary"]["total"] == 1
assert Path(report["output_dir"]).exists()
print("PASS")
