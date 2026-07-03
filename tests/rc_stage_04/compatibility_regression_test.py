from pathlib import Path
from translation.consistency_audit import TranslationConsistencyAuditor

def test_rc4_preserves_rc3_and_compatibility():
    result = TranslationConsistencyAuditor(Path.cwd()).run()
    assert result["audit"]["rc3_performance_baseline_preserved"] is True
    assert result["baseline"]["validation"]["public_api_changed"] is False
