from pathlib import Path
from release_candidate.validation import ReleaseCandidateValidator


def test_rc5_does_not_add_product_features():
    result = ReleaseCandidateValidator(Path.cwd()).run()
    assert result["validation"]["product_feature_added"] is False
    assert result["validation"]["public_api_changed"] is False
    assert result["validation"]["release_candidate_ready"] is True
