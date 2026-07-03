from pathlib import Path
from release_candidate.validation import ReleaseCandidateValidator, RC_VALIDATION_CRITERIA


def test_release_candidate_validation_passes():
    result = ReleaseCandidateValidator(Path.cwd()).run()
    assert result["passed"] is True
    assert result["status"] == "PASS"
    assert result["validation"]["public_api_changed"] is False
    assert result["validation"]["product_feature_added"] is False
    assert result["validation"]["rc_candidate_ready"] is True
    assert len(result["baseline"]["criteria"]) == len(RC_VALIDATION_CRITERIA)
