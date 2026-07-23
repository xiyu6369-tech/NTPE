from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Policy (immutable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionPolicy:
    """Immutable policy for Stage 6.2 consumption preparation.

    All fields are frozen. The default policy enforces strict single-unit,
    offline-only consumption without durable enforcement.
    """

    require_single_unit: bool = True
    require_unit_count_exactly_one: bool = True
    require_caller_confirmation: bool = True
    require_explicit_scope: bool = True
    forbid_execution: bool = True
    forbid_durable_registry_claim: bool = True
    forbid_durable_reuse_prevention_claim: bool = True
    forbid_enablement: bool = True
    forbid_writes: bool = True
    require_freeze_gate: bool = True
    require_authorization_not_consumed: bool = True
    require_non_reusable: bool = True

    def __post_init__(self) -> None:
        if self.require_unit_count_exactly_one is not True:
            raise ValueError("require_unit_count_exactly_one must be True")
        if self.forbid_execution is not True:
            raise ValueError("forbid_execution must be True")
        if self.forbid_durable_registry_claim is not True:
            raise ValueError("forbid_durable_registry_claim must be True")
        if self.forbid_durable_reuse_prevention_claim is not True:
            raise ValueError("forbid_durable_reuse_prevention_claim must be True")
        if self.forbid_enablement is not True:
            raise ValueError("forbid_enablement must be True")
        if self.forbid_writes is not True:
            raise ValueError("forbid_writes must be True")


DEFAULT_POLICY = ControlledRuntimeAuthorizationConsumptionPolicy()


# ---------------------------------------------------------------------------
# Scope builder
# ---------------------------------------------------------------------------

def exact_consumption_scope(
    authorization_id: str,
    authorization_request_fingerprint: str,
    authorization_decision_fingerprint: str,
    execution_plan_fingerprint: str,
    selected_adapter_index: int,
    unit_count: int,
) -> str:
    """Build a deterministic consumption scope binding.

    Returns a deterministic, immutable scope string that exactly binds:
    - authorization ID
    - authorization request fingerprint
    - authorization decision fingerprint
    - execution plan fingerprint
    - selected adapter index
    - unit count
    """
    if selected_adapter_index is True or selected_adapter_index is False:
        raise TypeError("selected_adapter_index must be int, got bool")
    if unit_count is True or unit_count is False:
        raise TypeError("unit_count must be int, got bool")
    if not authorization_id:
        raise ValueError("authorization_id must be non-empty")
    return (
        f"consumption:{authorization_id}"
        f":auth_req={authorization_request_fingerprint}"
        f":auth_dec={authorization_decision_fingerprint}"
        f":plan={execution_plan_fingerprint}"
        f":index={selected_adapter_index}"
        f":units={unit_count}"
    )