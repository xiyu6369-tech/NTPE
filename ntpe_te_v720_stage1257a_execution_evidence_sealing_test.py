from __future__ import annotations

import json
from tools.generate_te_v720_stage1257a_execution_evidence_sealing import build_artifacts


def test_stage1257a_root_acceptance() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    assert artifacts["sealing_summary.json"]["status"] == "PASS"
    assert artifacts["final_activation_decision.json"]["activation_decision"] == "final_fail_closed"


if __name__ == "__main__":
    print("TE_V720_STAGE1257A_ROOT_ACCEPTANCE=PASS")
    test_stage1257a_root_acceptance()
