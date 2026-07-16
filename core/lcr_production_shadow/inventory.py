from __future__ import annotations


INTEGRATION_POINTS = (
    ("runtime_entry", "ntpe_production_translate.py", "main", "production runtime entrypoint", True, "high", "not_recommended"),
    ("request_construction", "core/ai_provider", "ProviderRequest", "translation request construction", True, "high", "not_recommended"),
    ("prompt_assembly", "core/prompt_builder.py", "PromptBuilder", "prompt assembly", True, "high", "not_recommended"),
    ("provider_boundary", "core/ai_provider", "complete", "provider invocation boundary", True, "critical", "not_recommended"),
    ("retry_boundary", "core/translation_reliability", "retry", "retry planning boundary", True, "high", "shadow_compare"),
    ("resume_journal", "core/translation_scheduler", "ResumeJournal", "resume truth", True, "high", "shadow_read"),
    ("chunk_result", "core/translation_engine", "ChunkResult", "chunk result model", True, "high", "shadow_read"),
    ("output_assembly", "core/translation_engine", "assemble", "output assembly", True, "critical", "shadow_read"),
    ("quality_gate", "core/translation_quality", "assess", "quality gate", True, "high", "shadow_compare"),
    ("cli_flags", "launcher_translate.py", "parse_args", "CLI flags", True, "high", "not_recommended"),
    ("config_loading", "core/config.py", "load", "config loading", True, "high", "shadow_read"),
    ("feature_flags", "core/lcr_production_shadow/feature_flags.py", "resolve_feature_flags", "isolated shadow flags", False, "low", "shadow_read"),
    ("observability", "core/logging_config.py", "logger", "logging and observability", True, "medium", "shadow_read"),
    ("cache", "core/chunk_cache_v2", "plan_chunk_reexecution", "cache planning", True, "high", "shadow_compare"),
    ("release_guards", "ntpe_validate.py", "main", "version and release guards", True, "high", "shadow_read"),
)


def build_integration_inventory() -> tuple[dict[str, object], ...]:
    return tuple({
        "integration_point_id": item[0], "module_path": item[1], "symbol": item[2],
        "current_role": item[3], "input_contract": "metadata-only defensive copy",
        "output_contract": "immutable shadow evidence", "mutable": False,
        "frozen": item[4], "risk_level": item[5], "lcr_candidate_modules": (),
        "shadow_read_possible": item[6] != "not_recommended", "active_write_required": False,
        "rollback_requirement": "kill switch and baseline preservation",
        "recommended_phase": item[6],
    } for item in INTEGRATION_POINTS)


DECISION_MATRIX = (
    ("character_memory_v2", "SHADOW_COMPUTE", 4, 1, 256, 0, 2),
    ("context_scene_memory", "SHADOW_COMPUTE", 5, 1, 512, 0, 2),
    ("chunk_cache_v2", "SHADOW_COMPARE", 4, 1, 0, 0, 2),
    ("dual_pass", "SHADOW_COMPUTE", 3, 3, 0, 1, 4),
    ("semantic_verification", "SHADOW_COMPUTE", 5, 2, 0, 0, 2),
    ("multilingual_profiles", "SHADOW_READ", 4, 1, 160, 0, 2),
    ("controlled_provider_routing", "SHADOW_COMPARE", 4, 2, 0, 1, 4),
)


def build_decision_matrix() -> tuple[dict[str, object], ...]:
    return tuple({"module": x[0], "decision": x[1], "direct_quality_value": x[2],
                  "runtime_cost": x[3], "prompt_token_cost": x[4],
                  "provider_request_cost": x[5], "failure_risk": x[6],
                  "rollback_method": "disable individual flag or global kill switch",
                  "activation_precondition": "manual approval after ready_for_shadow_hook"} for x in DECISION_MATRIX)
