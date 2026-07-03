from pathlib import Path
from translation.consistency_audit import TranslationConsistencyAuditor, CONSISTENCY_RULES

def test_translation_consistency_audit_passes():
    result = TranslationConsistencyAuditor(Path.cwd()).run()
    assert result["passed"] is True
    assert result["status"] == "PASS"
    assert result["baseline"]["validation"]["translation_consistency_regression_detected"] is False
    assert result["baseline"]["validation"]["public_api_changed"] is False
    assert result["baseline"]["validation"]["product_feature_added"] is False
    assert len(result["baseline"]["rules"]) == len(CONSISTENCY_RULES)
