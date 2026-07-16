from __future__ import annotations

from .models import RollbackStep


ROLLBACK_ACTIONS = (
    (0, "any shadow safety event", "set kill switch true"),
    (1, "single module anomaly", "disable individual shadow module"),
    (2, "cross-module anomaly", "disable all LCR shadow flags"),
    (3, "configuration anomaly", "restore baseline configuration"),
    (4, "integration defect", "revert future integration commit"),
)


def build_rollback_plan(level: int | None = None) -> tuple[RollbackStep, ...]:
    if level is not None and level not in range(5):
        raise ValueError("invalid rollback level")
    rows = ROLLBACK_ACTIONS if level is None else (ROLLBACK_ACTIONS[level],)
    return tuple(RollbackStep(number, trigger, action, "baseline flow remains authoritative",
                              ("shadow evidence", "TIC golden evidence"), "none",
                              "verify flags and baseline fingerprint") for number, trigger, action in rows)
