from __future__ import annotations

FREEZE_VERSION = "7.0.0-stage08.4"
STAGE08_FREEZE_CONTRACT = {
    "activation_policy": "7.0.0-stage08.1",
    "profile_budget": "7.0.0-stage08.2",
    "strategy_selection": "7.0.0-stage08.3",
    "deterministic_rollout": "sha256-10000-buckets",
    "package_bound_anchor": "7.0.0-stage07.4",
    "admission_gate": "fail-closed",
    "metrics_schema": FREEZE_VERSION,
    "rollback_contract": FREEZE_VERSION,
    "kill_switch": "next-chunk-immediate",
    "maximum_rollout_percent": 5,
    "provider_calls_added": 0,
    "te_v6_backward_compatible": True,
    "te_v7_final_release": False,
}


def validate_freeze_contract() -> tuple[str, ...]:
    blockers: list[str] = []
    if STAGE08_FREEZE_CONTRACT["maximum_rollout_percent"] != 5:
        blockers.append("rollout-cap-drift")
    if STAGE08_FREEZE_CONTRACT["provider_calls_added"] != 0:
        blockers.append("provider-call-invariant-drift")
    if STAGE08_FREEZE_CONTRACT["te_v7_final_release"] is not False:
        blockers.append("final-release-misclassification")
    return tuple(blockers)
