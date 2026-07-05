# =====================================================
# NTPE 1.2 Professional
# Stage-10.7 Project Validator Test
# =====================================================

from ntpe_validate import run_validation


def test_ntpe_validator_has_no_failures():
    results = run_validation(include_pytest=False)
    failures = [r for r in results if r.status == "FAIL"]
    assert failures == []


def test_ntpe_validator_reports_required_checks():
    results = run_validation(include_pytest=False)
    names = {r.name for r in results}
    assert "Required directories" in names
    assert "Legacy entrypoints" in names
    assert "Core imports" in names
    assert "Python compile" in names
