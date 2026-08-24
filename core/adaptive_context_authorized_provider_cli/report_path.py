from __future__ import annotations

from pathlib import Path

from core.production_runtime.manifest import get_te_v7_stage_path


def resolve_stage10_report_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    allowed = (
        get_te_v7_stage_path(base, "te_v7_stage10"),
        get_te_v7_stage_path(base, "te_v7_stage106"),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("authorized-cli-report-path-outside-stage10-sandbox")
    protected = get_te_v7_stage_path(base, "te_v7_stage09")
    if target == protected or protected in target.parents:
        raise ValueError("authorized-cli-stage09-overwrite-forbidden")
    return target
