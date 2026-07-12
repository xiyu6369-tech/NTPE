from __future__ import annotations

import os

STOP_ENV = "NTPE_TE_V7_ACE_CANARY_STOP_AFTER_TARGET"
STOP_MARKER = "TE_V7_CANARY_TARGET_COMPLETE"


class CanaryTargetComplete(RuntimeError):
    """Controlled stop raised before the first chunk after the canary target."""


def should_stop_before_chunk(chunk_index: int, target_chunk: int) -> bool:
    enabled = str(os.environ.get(STOP_ENV, "0")).strip().lower() in {"1", "true", "yes", "on"}
    return enabled and int(chunk_index) > max(1, int(target_chunk))


def target_complete_error(target_chunk: int) -> CanaryTargetComplete:
    return CanaryTargetComplete(f"{STOP_MARKER}:target_chunk={max(1, int(target_chunk))}")


def is_target_complete_result(result: dict[str, object]) -> bool:
    for record in result.get("records", []) if isinstance(result, dict) else []:
        if isinstance(record, dict) and STOP_MARKER in str(record.get("error", "")):
            return True
    return STOP_MARKER in str(result.get("error", "")) if isinstance(result, dict) else False
