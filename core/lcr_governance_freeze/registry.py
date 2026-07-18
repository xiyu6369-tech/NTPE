from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    batch: str
    component: str
    schema_version: str
    status: str
    frozen: bool
    active_integration: bool
    production_write_allowed: bool
    provider_execution_allowed: bool
    public_api: tuple[str, ...]
    manifest_path: str
    audit_path: str
    rollback_strategy: str
    dependencies: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "batch": self.batch,
            "component": self.component,
            "schema_version": self.schema_version,
            "status": self.status,
            "frozen": self.frozen,
            "active_integration": self.active_integration,
            "production_write_allowed": self.production_write_allowed,
            "provider_execution_allowed": self.provider_execution_allowed,
            "public_api": list(self.public_api),
            "manifest_path": self.manifest_path,
            "audit_path": self.audit_path,
            "rollback_strategy": self.rollback_strategy,
            "dependencies": list(self.dependencies),
        }


def _capability(
    capability_id: str,
    batch: str,
    component: str,
    schema_version: str,
    public_api: tuple[str, ...],
    manifest_path: str,
    audit_path: str,
    rollback_strategy: str,
    dependencies: tuple[str, ...] = (),
) -> CapabilityRecord:
    return CapabilityRecord(
        capability_id=capability_id,
        batch=batch,
        component=component,
        schema_version=schema_version,
        status="governance_frozen",
        frozen=True,
        active_integration=False,
        production_write_allowed=False,
        provider_execution_allowed=False,
        public_api=public_api,
        manifest_path=manifest_path,
        audit_path=audit_path,
        rollback_strategy=rollback_strategy,
        dependencies=dependencies,
    )


CAPABILITY_REGISTRY: tuple[CapabilityRecord, ...] = (
    _capability(
        "character_memory_v2", "2", "core.character_memory_v2", "2.0",
        ("add_or_merge_memory", "select_prompt_eligible_memories", "rollback_memory"),
        "audits/legacy_capability_recovery/batch2/LCR_BATCH2_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch2/LCR_BATCH2_BOUNDARY_REPORT.json",
        "retain production character store; discard or roll back isolated memory records",
    ),
    _capability(
        "context_scene_memory", "3", "core.context_scene_memory", "1.0",
        ("select_context_for_translation", "rollback_context", "rollback_scene"),
        "audits/legacy_capability_recovery/batch3/LCR_BATCH3_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch3/LCR_BATCH3_BOUNDARY_REPORT.json",
        "retain production context store; discard isolated context and scene records",
        ("character_memory_v2",),
    ),
    _capability(
        "chunk_cache_v2", "4", "core.chunk_cache_v2", "2.0",
        ("lookup_chunk_cache", "reconcile_cache_with_resume", "rollback_cache_entry"),
        "audits/legacy_capability_recovery/batch4/LCR_BATCH4_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch4/LCR_BATCH4_BOUNDARY_REPORT.json",
        "retain production cache and resume; invalidate isolated cache entry",
    ),
    _capability(
        "dual_pass_translation", "5", "core.dual_pass_translation", "1.0",
        ("build_dual_pass_execution_plan", "create_polish_candidate", "apply_polish_rollback"),
        "audits/legacy_capability_recovery/batch5/LCR_BATCH5_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch5/LCR_BATCH5_BOUNDARY_REPORT.json",
        "discard polish candidate and retain production translation",
        ("chunk_cache_v2",),
    ),
    _capability(
        "post_polish_semantic_verification", "6", "core.post_polish_semantic_verification", "1.0",
        ("verify_post_polish_semantics", "verify_dual_pass_polish", "build_rollback_recommendation"),
        "audits/legacy_capability_recovery/batch6/LCR_BATCH6_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch6/LCR_BATCH6_BOUNDARY_REPORT.json",
        "semantic failure rejects candidate and retains production translation",
        ("dual_pass_translation",),
    ),
    _capability(
        "multilingual_profiles", "7", "core.multilingual_profiles", "1.0",
        ("select_language_profile", "get_language_profile", "build_semantic_verification_hints"),
        "audits/legacy_capability_recovery/batch7/LCR_BATCH7_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch7/LCR_BATCH7_BOUNDARY_REPORT.json",
        "fall back to frozen common target policy without production write",
        ("character_memory_v2", "context_scene_memory", "post_polish_semantic_verification"),
    ),
    _capability(
        "controlled_provider_routing", "8", "core.controlled_provider_routing", "1.0",
        ("select_provider_route", "build_provider_execution_plan", "evaluate_retry_eligibility"),
        "audits/legacy_capability_recovery/batch8/LCR_BATCH8_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch8/LCR_BATCH8_BOUNDARY_REPORT.json",
        "fail closed before Provider execution",
        ("dual_pass_translation", "post_polish_semantic_verification", "multilingual_profiles"),
    ),
    _capability(
        "offline_golden_tic_validation", "9", "core.lcr_offline_validation", "1.0",
        ("run_validation_suite", "evaluate_lcr_offline_readiness"),
        "audits/legacy_capability_recovery/batch9/LCR_BATCH9_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch9/LCR_BATCH9_BOUNDARY_REPORT.json",
        "preserve frozen fixtures and report manual review when evidence is insufficient",
        ("character_memory_v2", "context_scene_memory", "chunk_cache_v2", "dual_pass_translation", "post_polish_semantic_verification", "multilingual_profiles", "controlled_provider_routing"),
    ),
    _capability(
        "production_shadow_planning", "10", "core.lcr_production_shadow", "1.0",
        ("run_lcr_production_shadow", "evaluate_activation_gate", "build_rollback_plan"),
        "audits/legacy_capability_recovery/batch10/LCR_BATCH10_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch10/LCR_BATCH10_BOUNDARY_REPORT.json",
        "disable all shadow feature flags and retain baseline",
        ("offline_golden_tic_validation",),
    ),
    _capability(
        "read_only_production_shadow_hook", "10.1", "core.lcr_production_shadow_hook", "1.0",
        ("run_read_only_lcr_shadow_hook", "resolve_hook_flags"),
        "audits/legacy_capability_recovery/batch10_1/LCR_BATCH101_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch10_1/LCR_BATCH101_BOUNDARY_REPORT.json",
        "kill switch disables the single read-only hook",
        ("production_shadow_planning",),
    ),
    _capability(
        "character_memory_shadow", "10.2", "core.lcr_production_shadow_hook.character_memory_shadow", "1.0",
        ("build_character_memory_shadow_input", "evaluate_character_memory_shadow"),
        "audits/legacy_capability_recovery/batch10_2/LCR_BATCH102_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch10_2/LCR_BATCH102_BOUNDARY_REPORT.json",
        "discard immutable shadow snapshot; production character store remains unchanged",
        ("character_memory_v2", "read_only_production_shadow_hook"),
    ),
    _capability(
        "context_scene_shadow", "10.3", "core.lcr_production_shadow_hook.context_scene_shadow", "1.0",
        ("build_context_scene_shadow_input", "evaluate_context_scene_shadow"),
        "audits/legacy_capability_recovery/batch10_3/LCR_BATCH103_PACKAGE_REPORT.json",
        "audits/legacy_capability_recovery/batch10_3/LCR_BATCH103_BOUNDARY_REPORT.json",
        "discard immutable shadow snapshot; production context store remains unchanged",
        ("context_scene_memory", "character_memory_shadow"),
    ),
    _capability(
        "dual_pass_semantic_shadow", "10.4", "core.lcr_production_shadow_hook.dual_pass_semantic_shadow", "1.0",
        ("build_dual_pass_semantic_shadow_input", "evaluate_dual_pass_semantic_shadow"),
        "audits/legacy_capability_recovery/batch10_4/LCR_BATCH104_FILE_INVENTORY.json",
        "audits/legacy_capability_recovery/batch10_4/LCR_BATCH104_BOUNDARY_REPORT.json",
        "discard candidate and retain production translation",
        ("dual_pass_translation", "post_polish_semantic_verification", "context_scene_shadow"),
    ),
    _capability(
        "explicit_pilot_authorization", "10.5", "core.lcr_production_shadow_hook.pilot_authorization", "1.0",
        ("validate_authorization", "prepare_bounded_dual_pass_pilot"),
        "audits/legacy_capability_recovery/batch10_5/LCR_BATCH105_PRODUCTION_HOOK_INVENTORY.json",
        "audits/legacy_capability_recovery/batch10_5/LCR_BATCH105_BOUNDARY_REPORT.json",
        "deny pilot preparation and retain production baseline",
        ("controlled_provider_routing", "dual_pass_semantic_shadow"),
    ),
    _capability(
        "single_chunk_execution_review", "10.6", "core.lcr_production_shadow_hook.single_chunk_dual_pass_executor", "1.0",
        ("execute_single_chunk_dual_pass_review", "validate_execution_authorization"),
        "audits/legacy_capability_recovery/batch10_6/LCR_BATCH106_FILE_INVENTORY.json",
        "audits/legacy_capability_recovery/batch10_6/LCR_BATCH106_BOUNDARY_REPORT.json",
        "discard review candidate and retain production translation",
        ("post_polish_semantic_verification", "explicit_pilot_authorization"),
    ),
    _capability(
        "real_provider_validation", "10.7", "core.lcr_production_shadow_hook.batch107_real_provider_validation", "1.0",
        ("validate_execution_package", "validate_package_authorization", "execute_batch107"),
        "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_FILE_INVENTORY.json",
        "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json",
        "consumed one-shot claim forbids re-execution; production baseline remains unchanged",
        ("controlled_provider_routing", "single_chunk_execution_review"),
    ),
    _capability(
        "provider_failure_characterization", "10.8", "core.provider_failure_characterization", "1.0",
        ("classify_failure", "execution_decision", "summarize_execution"),
        "audits/legacy_capability_recovery/batch10_8/LCR_BATCH108_FILE_INVENTORY.json",
        "audits/legacy_capability_recovery/batch10_8/LCR_BATCH108_BOUNDARY_REPORT.json",
        "fail closed, require manual review, and retain production state",
        ("real_provider_validation",),
    ),
    _capability(
        "provider_failure_policy_freeze", "10.9", "core.provider_failure_characterization.freeze", "1.0",
        ("get_provider_failure_policy_freeze_metadata", "validate_provider_failure_policy_freeze"),
        "manifests/lcr_batch109_provider_failure_policy_freeze_manifest.json",
        "audits/legacy_capability_recovery/batch10_9/LCR_BATCH109_BOUNDARY_REPORT.json",
        "reject policy drift; restore the Batch 10.9 frozen source baseline",
        ("provider_failure_characterization",),
    ),
)

CAPABILITIES_BY_ID: Mapping[str, CapabilityRecord] = MappingProxyType(
    {item.capability_id: item for item in CAPABILITY_REGISTRY}
)


def get_capability(capability_id: str) -> CapabilityRecord:
    return CAPABILITIES_BY_ID[capability_id]


def list_capabilities() -> tuple[CapabilityRecord, ...]:
    return CAPABILITY_REGISTRY
