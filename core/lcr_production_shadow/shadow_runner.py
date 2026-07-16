from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Mapping

from .feature_flags import KILL_SWITCH, resolve_feature_flags
from .models import ProductionShadowInput, ProductionShadowResult
from .serialization import deterministic_fingerprint


MODULE_FLAGS = (
    ("character_memory", "LCR_CHARACTER_MEMORY_SHADOW"),
    ("context_scene", "LCR_CONTEXT_SCENE_SHADOW"),
    ("chunk_cache", "LCR_CHUNK_CACHE_SHADOW"),
    ("dual_pass", "LCR_DUAL_PASS_SHADOW"),
    ("semantic_verification", "LCR_SEMANTIC_VERIFICATION_SHADOW"),
    ("multilingual_profile", "LCR_MULTILINGUAL_PROFILE_SHADOW"),
    ("provider_routing", "LCR_PROVIDER_ROUTING_SHADOW"),
)


def run_lcr_production_shadow(
    item: ProductionShadowInput,
    *,
    flags: Mapping[str, object] | None = None,
    module_overrides: Mapping[str, Callable[[ProductionShadowInput], Mapping[str, Any]]] | None = None,
) -> ProductionShadowResult:
    resolved = resolve_feature_flags(flags if flags is not None else item.feature_flag_state)
    input_fp = deterministic_fingerprint(item)
    empty: dict[str, Any] = {}
    base = ProductionShadowResult("shadow-" + input_fp[:20], input_fp, (), empty, empty, empty, empty,
                                  False, empty, {"prepare_only": True, "executed": False, "network_requests": 0},
                                  "skipped")
    if resolved[KILL_SWITCH]:
        return replace(base, readiness_result="blocked", blocking_reasons=("kill_switch_active",),
                       deterministic_fingerprint=deterministic_fingerprint({"input": input_fp, "status": "blocked"}))
    if not resolved["LCR_SHADOW_ENABLED"]:
        return replace(base, deterministic_fingerprint=deterministic_fingerprint({"input": input_fp, "status": "skipped"}))
    overrides = module_overrides or {}
    views: dict[str, Mapping[str, Any]] = {}
    modules: list[str] = []
    warnings: list[str] = []
    for module, flag in MODULE_FLAGS:
        if not resolved[flag]:
            continue
        modules.append(module)
        try:
            views[module] = dict(overrides[module](item)) if module in overrides else {"eligible": True, "applied": False}
        except Exception:
            views[module] = {"eligible": False, "applied": False}
            warnings.append(f"{module}_degraded")
    status = "degraded" if warnings else "completed"
    result = replace(
        base, modules_evaluated=tuple(modules), character_memory_view=views.get("character_memory", empty),
        context_scene_view=views.get("context_scene", empty), cache_decision=views.get("chunk_cache", empty),
        dual_pass_decision=views.get("dual_pass", empty),
        semantic_verification_requirement=bool(views.get("semantic_verification", {}).get("required", False)),
        language_profile_view=views.get("multilingual_profile", empty),
        provider_route_view={**base.provider_route_view, **views.get("provider_routing", {})},
        readiness_result=status, warnings=tuple(warnings), provider_requests_planned=0,
        provider_requests_executed=0,
    )
    return replace(result, deterministic_fingerprint=deterministic_fingerprint({
        "input": input_fp, "modules": modules, "views": views, "status": status, "warnings": warnings,
    }))
