from __future__ import annotations

import json

from tools.generate_te_v720_stage1259_name_resolution_contract_remediation import build_artifacts


def test_stage1259_root_acceptance() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    summary = artifacts["preparation_summary.json"]
    assert summary["status"] == "PASS"
    assert summary["offline_status"] == "name_resolution_contract_remediation_prepared"
    assert summary["provider_requests"] == 0 and summary["network_requests"] == 0
    assert summary["next_canary_authorized"] is False


if __name__ == "__main__":
    test_stage1259_root_acceptance()
    print("TE_V720_STAGE1259_ROOT_ACCEPTANCE=PASS")
