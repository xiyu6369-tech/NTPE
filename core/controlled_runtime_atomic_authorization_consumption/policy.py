"""Immutable Stage 6.3 policy."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AtomicAuthorizationConsumptionPolicy:
    require_single_execution: bool = True
    required_unit_count: int = 1
    require_caller_confirmation: bool = True
    require_non_reusable_authorization: bool = True
    require_explicit_registry: bool = True
    forbid_execution: bool = True
    forbid_non_registry_writes: bool = True
    sqlite_busy_timeout_ms: int = 5000

    def __post_init__(self) -> None:
        if self.required_unit_count != 1 or type(self.required_unit_count) is not int:
            raise ValueError("required_unit_count must be integer 1")
        for name in (
            "require_single_execution", "require_caller_confirmation",
            "require_non_reusable_authorization", "require_explicit_registry",
            "forbid_execution", "forbid_non_registry_writes",
        ):
            if getattr(self, name) is not True:
                raise ValueError(f"{name} must remain true")
