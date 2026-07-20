from __future__ import annotations

import json
from tools.generate_te_v720_stage1257a_execution_evidence_sealing import build_artifacts


def test_stage1257a_integration_post_execution_state_is_fail_closed() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    historical = artifacts["test_state_isolation.json"]["historical_post_execution_fixture"]
    assert historical["claim_replay_rejected"] is True
    assert artifacts["historical_execution_seal.json"]["baseline_timeout"] is True
    assert artifacts["historical_execution_seal.json"]["candidate_success"] is False
