from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ProductionShadowResult


def validate_shadow_result(result: ProductionShadowResult) -> tuple[str, ...]:
    errors: list[str] = []
    if result.baseline_changed:
        errors.append("baseline_changed")
    if result.production_output_changed:
        errors.append("production_output_changed")
    if result.provider_requests_executed:
        errors.append("provider_requests_executed")
    if result.provider_route_view.get("executed") or result.provider_route_view.get("network_requests", 0):
        errors.append("provider_boundary_violated")
    return tuple(errors)


def resolve_allowed_path(path: Path, allowed_root: Path) -> Path:
    root = allowed_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes allowed root") from exc
    if path.is_symlink():
        raise ValueError("symlink inputs are not allowed")
    return resolved
