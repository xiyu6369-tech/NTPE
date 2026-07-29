# RM-3.2 Repository Migration Validation Report

**Generated:** 2026-07-27T22:21:00+08:00
**Stage:** RM-3.2 — Evidence Verification
**Total Files Validated:** 337

## Overview

This report validates every classification produced by RM-2.4 before any repository migration begins. 
Each file is evidence-verified against the following rules:

1. **Documentation-only references must not automatically require wrappers.**
2. **Historical artifacts must not automatically block migration.**
3. **Runtime imports** (`imported_by_other_modules`) require wrappers.
4. **Subprocess execution** references require wrappers.
5. **Operational tool references** (e.g., `tools/generate_rm_2_3b_evidence.py`) count as KEEP_ROOT justification,

## Classification Summary

| Classification | Original Count | Validated Count | Change |
| --- | --- | --- | --- |
| KEEP_ROOT | 15 | 15 | 0 |
| ARCHIVE_ONLY | 291 | 192 | -99 |
| MOVE_WITH_WRAPPER | 31 | 2 | -29 |
| SAFE_MOVE | 0 | 29 | +29 |
| REVIEW | 0 | 99 | +99 |

## Classification Changes

| Change | Count |
| --- | --- |
| MOVE_WITH_WRAPPER -> SAFE_MOVE | 29 |
| ARCHIVE_ONLY -> REVIEW | 99 |

## Validation Issues Found: 128

## Files with Classification Changes

### `launcher_adaptive_recovery.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_analyzer.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_character_db.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_expansion_plan.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_glossary.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_kb.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_memory.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_pipeline_recovery.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_pipeline_v1.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_profile.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_prompt_builder.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_quality_benchmark.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_retranslate_chunk.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_semantic_repair.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `launcher_style_expansion.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lcr_batch101_production_shadow_hook_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch10_production_shadow_planning_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch3_context_scene_memory_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch4_chunk_cache_v2_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch5_dual_pass_prototype_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch7_multilingual_profiles_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch8_controlled_provider_routing_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_lcr_batch9_offline_golden_tic_validation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_long_run_recovery.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_compatibility.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_final_validation.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_freeze.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_performance.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_quality.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_rc_regression.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_release_candidate.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_runtime_freeze.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_stable_complete.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_stable_finalization.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_lts_stable_preparation.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_plugin_marketplace.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Documentation-only/artifact-only references detected; wrapper not required per RM-3.2 rules
- **Evidence:** Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_provider_benchmark_session.py`
- **Original:** MOVE_WITH_WRAPPER
- **Validated:** SAFE_MOVE
- **Issues:** Only test-import dependencies detected; no runtime production dependency
- **Evidence:** Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- **Recommendation:** Move to target directory without wrapper. Documentation references should be updated to point to new location; artifact references are historical and do not require runtime compatibility.

### `ntpe_ps01_literary_prompt_engine_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_stage14_6_provider_security_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_stage18_13_translation_quality_stabilization_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_stage18_6_documentation_center_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_stage18_8_enterprise_deployment_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v30_stage01_prompt_intelligence_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v30_stage021_naturalness_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v30_stage022_runtime_speed_policy_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v30_stage02_context_intelligence_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_scheduler_layer_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage311_scheduler_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage312_retry_queue_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage313_result_collector_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage314_resume_journal_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage315_performance_dashboard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v31_stage316_performance_regression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_runtime_scheduler_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_stage321_runtime_scheduler_adapter_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_stage323_existing_scheduler_injection_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_stage324_runtime_scheduler_state_bridge_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v32_stage325_runtime_scheduler_resume_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_runtime_integration_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_stage331_runtime_integration_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_stage332_runtime_integration_feature_flag_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_stage333_runtime_integration_disabled_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_stage334_runtime_integration_mock_orchestrator_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v33_stage335_runtime_integration_boundary_regression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v34_runtime_optin_hook_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v34_stage341_runtime_optin_hook_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v34_stage342_runtime_optin_hook_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v34_stage343_runtime_optin_hook_mock_bridge_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v34_stage344_runtime_optin_hook_boundary_regression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v35_runtime_disabled_trial_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v35_stage351_runtime_disabled_trial_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v35_stage352_runtime_disabled_trial_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v35_stage353_runtime_disabled_trial_mock_bridge_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v35_stage354_runtime_disabled_trial_boundary_regression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v36_runtime_safe_hook_preflight_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v36_stage361_runtime_safe_hook_preflight_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v36_stage362_runtime_safe_hook_preflight_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v36_stage363_runtime_safe_hook_preflight_mock_bridge_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v37_runtime_readiness_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v37_stage371_runtime_readiness_gate_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v37_stage372_runtime_readiness_gate_evaluator_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v37_stage373_runtime_readiness_evidence_collector_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v37_stage374_runtime_readiness_decision_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v38_stage382_controlled_runtime_trial_admission_gate_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v44_stage442_controlled_execution_admission_gate_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v521_timeout_propagation_fix_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v530_quality_runtime_integration_phase1_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v5311_paragraph_coverage_corroboration_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v531_unified_quality_gate_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v532_semantic_repetition_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v540_smart_local_repair_pipeline_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v5532_adaptive_retry_failure_fallback_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v553_adaptive_prompt_feedback_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v600_stage05_adaptive_retry_decision_engine_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v600_stage06_discipline_runtime_orchestrator_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v600_stage08_translation_discipline_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage051_mutable_validation_artifact_integrity_fix_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage061_canary_validation_test_hardening_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage06_ace_canary_production_validation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage073_prompt_context_anchor_contract_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v700_stage07_ace_canary_resume_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has PRODUCTION runtime import/subprocess dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_milestone_a_translation_quality_integration_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1254_prompt_contract_preservation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1255_prompt_canary_readiness_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1256_prompt_verification_canary_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1257_prompt_verification_canary_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1257a_execution_evidence_sealing_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1258_candidate_structural_verification_canary_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1258a_candidate_structural_failure_sealing_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_te_v720_stage1259_name_resolution_contract_remediation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v11_translation_quality_foundation_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v12_literary_style_engine_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v13_speed_prompt_compression_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v16_semantic_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v18_character_tone_api_stability_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v19_stability_repetition_guard_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v20_quality_lock_baseline_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

### `ntpe_ter_v24_runtime_provider_stability_test.py`
- **Original:** ARCHIVE_ONLY
- **Validated:** REVIEW
- **Issues:** File has test framework dependency but is classified as ARCHIVE_ONLY
- **Evidence:** Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- **Recommendation:** Classification needs manual review. Do not move or archive until resolution.

## KEEP_ROOT Files (Maintain at Repository Root)

- `launcher_pipeline.py`
- `launcher_pipeline_production.py`
- `launcher_translate.py`
- `ntpe_authorized_provider_invocation.py`
- `ntpe_batch_monitor.py`
- `ntpe_controlled_real_provider_retry.py`
- `ntpe_launcher.py`
- `ntpe_production_translate.py`
- `ntpe_provider_audit.py`
- `ntpe_provider_setup.py`
- `ntpe_provider_verify.py`
- `ntpe_single_real_provider_invocation.py`
- `ntpe_translate_batch.py`
- `ntpe_translate_txt.py`
- `ntpe_validate.py`

## SAFE_MOVE Files (Move Without Wrapper)

These files were previously classified as MOVE_WITH_WRAPPER but evidence shows no runtime dependency.

- `launcher_adaptive_recovery.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_analyzer.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_character_db.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_expansion_plan.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_glossary.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_kb.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_memory.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_pipeline_recovery.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_pipeline_v1.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_profile.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_prompt_builder.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_quality_benchmark.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_retranslate_chunk.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_semantic_repair.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `launcher_style_expansion.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `ntpe_long_run_recovery.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_rc_compatibility.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `ntpe_lts_rc_final_validation.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_rc_freeze.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_rc_performance.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `ntpe_lts_rc_quality.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_rc_regression.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `ntpe_lts_release_candidate.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_runtime_freeze.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_stable_complete.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_stable_finalization.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_lts_stable_preparation.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.
- `ntpe_plugin_marketplace.py`: Only documentation, config, and/or artifact references detected. Per RM-3.2 rules: documentation-only references do not automatically require wrappers. File can be safely moved without wrapper.
- `ntpe_provider_benchmark_session.py`: Test imports only. Per RM-3.2 rules, test dependencies should not automatically require wrappers if no production runtime dependency exists. File can be safely moved.

## ARCHIVE_ONLY Files (192 files)

192 files classified as ARCHIVE_ONLY (historical test/benchmark/stage-specific files).

## REVIEW Files (Require Manual Review)

- `ntpe_lcr_batch101_production_shadow_hook_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch10_production_shadow_planning_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch3_context_scene_memory_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch4_chunk_cache_v2_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch5_dual_pass_prototype_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch7_multilingual_profiles_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch8_controlled_provider_routing_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_lcr_batch9_offline_golden_tic_validation_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ps01_literary_prompt_engine_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_stage14_6_provider_security_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_stage18_13_translation_quality_stabilization_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_stage18_6_documentation_center_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_stage18_8_enterprise_deployment_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v30_stage01_prompt_intelligence_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v30_stage021_naturalness_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v30_stage022_runtime_speed_policy_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v30_stage02_context_intelligence_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_scheduler_layer_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage311_scheduler_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage312_retry_queue_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage313_result_collector_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage314_resume_journal_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage315_performance_dashboard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v31_stage316_performance_regression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_runtime_scheduler_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_stage321_runtime_scheduler_adapter_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_stage323_existing_scheduler_injection_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_stage324_runtime_scheduler_state_bridge_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v32_stage325_runtime_scheduler_resume_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_runtime_integration_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_stage331_runtime_integration_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_stage332_runtime_integration_feature_flag_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_stage333_runtime_integration_disabled_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_stage334_runtime_integration_mock_orchestrator_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v33_stage335_runtime_integration_boundary_regression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v34_runtime_optin_hook_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v34_stage341_runtime_optin_hook_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v34_stage342_runtime_optin_hook_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v34_stage343_runtime_optin_hook_mock_bridge_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v34_stage344_runtime_optin_hook_boundary_regression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v35_runtime_disabled_trial_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v35_stage351_runtime_disabled_trial_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v35_stage352_runtime_disabled_trial_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v35_stage353_runtime_disabled_trial_mock_bridge_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v35_stage354_runtime_disabled_trial_boundary_regression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v36_runtime_safe_hook_preflight_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v36_stage361_runtime_safe_hook_preflight_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v36_stage362_runtime_safe_hook_preflight_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v36_stage363_runtime_safe_hook_preflight_mock_bridge_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v37_runtime_readiness_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v37_stage371_runtime_readiness_gate_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v37_stage372_runtime_readiness_gate_evaluator_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v37_stage373_runtime_readiness_evidence_collector_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v37_stage374_runtime_readiness_decision_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v38_stage382_controlled_runtime_trial_admission_gate_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v44_stage442_controlled_execution_admission_gate_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v521_timeout_propagation_fix_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v530_quality_runtime_integration_phase1_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v5311_paragraph_coverage_corroboration_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v531_unified_quality_gate_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v532_semantic_repetition_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v540_smart_local_repair_pipeline_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v5532_adaptive_retry_failure_fallback_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v553_adaptive_prompt_feedback_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v600_stage05_adaptive_retry_decision_engine_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v600_stage06_discipline_runtime_orchestrator_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v600_stage08_translation_discipline_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v700_stage051_mutable_validation_artifact_integrity_fix_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage061_canary_validation_test_hardening_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage06_ace_canary_production_validation_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage071_manifest_chain_decoupling_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage073_prompt_context_anchor_contract_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v700_stage07_ace_canary_resume_test.py`: Has production runtime dependency; ARCHIVE_ONLY classification may be incorrect. File needs manual review before archiving.
- `ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_milestone_a_translation_quality_integration_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1254_prompt_contract_preservation_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1255_prompt_canary_readiness_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1256_prompt_verification_canary_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1257_prompt_verification_canary_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1257a_execution_evidence_sealing_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1258_candidate_structural_verification_canary_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1258a_candidate_structural_failure_sealing_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_te_v720_stage1259_name_resolution_contract_remediation_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v11_translation_quality_foundation_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v12_literary_style_engine_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v13_speed_prompt_compression_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v16_semantic_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v18_character_tone_api_stability_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v19_stability_repetition_guard_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v20_quality_lock_baseline_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
- `ntpe_ter_v24_runtime_provider_stability_test.py`: Test verification dependency detected; may need relocation instead of archiving. Needs manual review.
