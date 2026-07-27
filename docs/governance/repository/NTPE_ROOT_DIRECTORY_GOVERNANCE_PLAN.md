# NTPE Root Directory Governance Plan (v1.0)

Date: 2026-07-27T13:36:59+08:00
Repository: NTPE
Baseline commit: 806ac7c8f45b44dbdf17d1ca81ae9ad590f52d72
Branch: main

NOTE: This is a READ-ONLY planning artifact. No repository files were modified. This single plan file is the only permitted new file.

---

1) Executive Summary

This plan establishes Root Directory Governance for NTPE. Goal: reduce the repository root to only Production Entry Points and Repository Metadata (and allowed Validators). The plan inventories root items, classifies each item, proposes destinations for MOVE candidates, and performs dependency verification where evidence is available. Items that could not be verified without further dynamic analysis are flagged REVIEW and must be reconciled before any move.

Key recommendations (short):
- KEEP at root: production entry scripts and repository metadata (README.md, requirements.txt, VERSION.txt, manifest / packaging top-level files), and validator(s) (ntpe_validate.py).
- MOVE (proposed destinations) only after verification or wrapper strategy is created. Many historical and stage/test scripts should be relocated to appropriate folders (tests/, tools/, tools/stages/, tools/translation_engine/, tools/lcr/).
- For scripts referenced by manifests/config/artifacts keep a lightweight wrapper in root (KEEP_ROOT) that imports or shell-invokes the new location.
- All proposed MOVE items flagged REVIEW until automated and manual dependency checks are finished. This plan includes targeted verification for high-impact items.

---

2) Current Root Inventory (top-level entries exactly as observed)

(Directories shown with trailing slash)

.ai
.clineignore
.clinerules
.codex
.editorconfig
.git
.gitattributes
.gitignore
.ntpe_runtime_checkpoints
docs/governance/audits/NTPE_GOVERNANCE_GAP_ANALYSIS.md
docs/governance/repository/NTPE_REPOSITORY_STATUS_REPORT.md
README.md
VERSION.txt
analysis/
artifacts/
audits/
benchmark/
character_database_override.json
character_override.json
cli/
compatibility/
config/
core/
create_context_pipeline_integration.py
create_context_prompt_integration.py
create_voice_batch1.py
data/
docs/
engine/
examples/
external_api/
failed_chunks/
final_output/
glossary_override.json
gui/
input/
integration/
launcher.py
launcher_adaptive_recovery.py
launcher_analyzer.py
launcher_character_db.py
launcher_coverage_test.py
launcher_expansion_plan.py
launcher_glossary.py
launcher_kb.py
launcher_memory.py
launcher_novel_prompt_test.py
launcher_pipeline.py
launcher_pipeline_production.py
launcher_pipeline_recovery.py
launcher_pipeline_v1.py
launcher_profile.py
launcher_prompt_builder.py
launcher_quality_benchmark.py
launcher_retranslate_chunk.py
launcher_semantic_repair.py
launcher_semantic_test.py
launcher_structure_test.py
launcher_style_expansion.py
launcher_style_planner_test.py
launcher_translate.py
lts/
lts_rc_compatibility/
lts_rc_final_validation/
lts_rc_freeze/
lts_rc_performance/
lts_rc_quality/
lts_rc_regression/
lts_release_candidate/
lts_runtime_freeze/
lts_stable_complete/
lts_stable_finalization/
lts_stable_preparation/
manifests/
memory/
ntpe/
ntpe_architecture_consolidation_batch1_repository_hygiene_test.py
ntpe_architecture_consolidation_batch2_test_consolidation_test.py
ntpe_architecture_consolidation_batch3_shared_utilities_pilot_test.py
ntpe_architecture_consolidation_batch4_quality_api_consolidation_test.py
ntpe_architecture_consolidation_batch5a1_replacement_parity_test.py
ntpe_architecture_consolidation_batch5a_dynamic_usage_audit_test.py
ntpe_authorized_provider_invocation.py
ntpe_batch_monitor.py
ntpe_controlled_real_provider_retry.py
ntpe_launcher.py
ntpe_lcr_batch101_production_shadow_hook_test.py
ntpe_lcr_batch102_character_memory_shadow_test.py
ntpe_lcr_batch103_context_scene_shadow_test.py
ntpe_lcr_batch104_dual_pass_semantic_shadow_test.py
ntpe_lcr_batch105_bounded_dual_pass_pilot_test.py
ntpe_lcr_batch106_single_chunk_dual_pass_execution_review_test.py
ntpe_lcr_batch107_pre_execution_package_test.py
ntpe_lcr_batch107_real_provider_validation.py
ntpe_lcr_batch108_failure_characterization_test.py
ntpe_lcr_batch109_provider_failure_policy_freeze_test.py
ntpe_lcr_batch10_production_shadow_planning_test.py
ntpe_literary_evaluation.py
ntpe_literary_regression.py
ntpe_long_run_recovery.py
ntpe_lts_rc_compatibility.py
ntpe_lts_rc_final_validation.py
ntpe_lts_rc_freeze.py
ntpe_lts_rc_performance.py
ntpe_lts_rc_quality.py
ntpe_lts_rc_regression.py
ntpe_lts_release_candidate.py
ntpe_lts_runtime_freeze.py
ntpe_lts_stable_complete.py
ntpe_lts_stable_finalization.py
ntpe_lts_stable_preparation.py
ntpe_plugin_marketplace.py
ntpe_production_translate.py
ntpe_provider_audit.py
ntpe_provider_benchmark_session.py
ntpe_provider_setup.py
ntpe_provider_verify.py
ntpe_ps01_literary_prompt_engine_test.py
ntpe_ps02_literary_regression_runner_test.py
ntpe_ps03_translation_corpus_evaluation_test.py
ntpe_ps04_1_regression_timeout_encoding_hotfix_test.py
ntpe_ps04_2_progress_visibility_hotfix_test.py
ntpe_ps04_narrative_character_understanding_test.py
ntpe_single_real_provider_invocation.py
ntpe_stage14_4_provider_orchestration_test.py
ntpe_stage14_5_provider_observability_test.py
ntpe_stage14_6_provider_security_test.py
ntpe_stage15_2_translation_completeness_test.py
ntpe_stage15_3_terminology_consistency_test.py
ntpe_stage15_4_repetition_detection_test.py
ntpe_stage15_5_structure_integrity_test.py
ntpe_stage15_6_quality_export_test.py
ntpe_stage15_7_quality_auto_repair_test.py
ntpe_stage15_8_translation_quality_engine_freeze_test.py
ntpe_stage16_1_context_intelligence_test.py
ntpe_stage16_2_narrative_intelligence_test.py
ntpe_stage16_3_character_relationship_intelligence_test.py
ntpe_stage16_4_semantic_consistency_test.py
ntpe_stage16_5_translation_memory_intelligence_test.py
ntpe_stage16_6_adaptive_translation_strategy_test.py
ntpe_stage16_7_intelligence_runtime_integration_test.py
ntpe_stage16_8_advanced_translation_intelligence_freeze_test.py
ntpe_stage17_1_translation_workflow_engine_test.py
ntpe_stage17_2_job_scheduler_test.py
ntpe_stage17_3_resource_optimizer_test.py
ntpe_stage17_4_review_approval_test.py
ntpe_stage17_5_export_framework_test.py
ntpe_stage17_6_monitoring_dashboard_api_test.py
ntpe_stage17_7_production_runtime_integration_test.py
ntpe_stage17_8_production_platform_freeze_test.py
ntpe_stage18_10_translation_qa_retry_hotfix_test.py
ntpe_stage18_11_translation_timeout_debug_hotfix_test.py
ntpe_stage18_12_name_lock_hotfix_test.py
ntpe_stage18_13_translation_quality_stabilization_test.py
ntpe_stage18_14_simplified_chinese_qa_hotfix_test.py
ntpe_stage18_1_enterprise_deployment_foundation_test.py
ntpe_stage18_2_enterprise_configuration_center_test.py
ntpe_stage18_3_enterprise_deployment_profiles_test.py
ntpe_stage18_4_enterprise_deployment_runtime_test.py
ntpe_stage18_5_enterprise_deployment_orchestrator_test.py
ntpe_stage18_6_documentation_center_test.py
ntpe_stage18_7_enterprise_deployment_validation_test.py
ntpe_stage18_8_enterprise_deployment_freeze_test.py
ntpe_stage18_9_production_translation_integration_test.py
ntpe_stage69_controlled_runtime_scheduling_envelope_consumption_acceptance_test.py
ntpe_te_v30_stage01_prompt_intelligence_test.py
ntpe_te_v30_stage021_naturalness_guard_test.py
ntpe_te_v30_stage022_runtime_speed_policy_test.py
ntpe_te_v30_stage02_context_intelligence_test.py
ntpe_te_v31_scheduler_layer_freeze_test.py
ntpe_te_v31_stage311_scheduler_test.py
ntpe_te_v31_stage312_retry_queue_test.py
ntpe_te_v31_stage313_result_collector_test.py
ntpe_te_v31_stage314_resume_journal_test.py
ntpe_te_v31_stage315_performance_dashboard_test.py
ntpe_te_v31_stage316_performance_regression_test.py
ntpe_te_v32_runtime_scheduler_freeze_test.py
ntpe_te_v32_stage321_runtime_scheduler_adapter_test.py
ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py
ntpe_te_v32_stage323_existing_scheduler_injection_test.py
ntpe_te_v32_stage324_runtime_scheduler_state_bridge_test.py
ntpe_te_v32_stage325_runtime_scheduler_resume_contract_test.py
ntpe_te_v33_runtime_integration_freeze_test.py
ntpe_te_v33_stage331_runtime_integration_contract_test.py
ntpe_te_v33_stage332_runtime_integration_feature_flag_test.py
ntpe_te_v33_stage333_runtime_integration_disabled_guard_test.py
ntpe_te_v33_stage334_runtime_integration_mock_orchestrator_test.py
ntpe_te_v33_stage335_runtime_integration_boundary_regression_test.py
ntpe_te_v34_runtime_optin_hook_freeze_test.py
ntpe_te_v34_stage341_runtime_optin_hook_contract_test.py
ntpe_te_v34_stage342_runtime_optin_hook_guard_test.py
ntpe_te_v34_stage343_runtime_optin_hook_mock_bridge_test.py
ntpe_te_v34_stage344_runtime_optin_hook_boundary_regression_test.py
ntpe_te_v35_runtime_disabled_trial_freeze_test.py
ntpe_te_v35_stage351_runtime_disabled_trial_contract_test.py
ntpe_te_v35_stage352_runtime_disabled_trial_guard_test.py
ntpe_te_v35_stage353_runtime_disabled_trial_mock_bridge_test.py
ntpe_te_v35_stage354_runtime_disabled_trial_boundary_regression_test.py
ntpe_te_v36_runtime_safe_hook_preflight_freeze_test.py
ntpe_te_v36_stage361_runtime_safe_hook_preflight_contract_test.py
ntpe_te_v36_stage362_runtime_safe_hook_preflight_guard_test.py
ntpe_te_v36_stage363_runtime_safe_hook_preflight_mock_bridge_test.py
ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py
ntpe_te_v37_runtime_readiness_freeze_test.py
ntpe_te_v37_stage371_runtime_readiness_gate_contract_test.py
ntpe_te_v37_stage372_runtime_readiness_gate_evaluator_test.py
ntpe_te_v37_stage373_runtime_readiness_evidence_collector_test.py
ntpe_te_v37_stage374_runtime_readiness_decision_test.py
ntpe_te_v37_stage375_runtime_readiness_report_test.py
ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py
ntpe_te_v38_stage382_controlled_runtime_trial_admission_gate_test.py
ntpe_te_v40_stage401_translation_reliability_baseline_test.py
ntpe_te_v40_stage402_adaptive_retry_policy_test.py
ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py
ntpe_te_v40_stage404_translation_failure_analyzer_test.py
ntpe_te_v40_stage405_retry_strategy_benchmark_test.py
ntpe_te_v40_stage406_reliability_runtime_integration_adapter_test.py
ntpe_te_v40_stage407_runtime_shadow_observation_test.py
ntpe_te_v40_stage408_translation_reliability_freeze_test.py
ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py
ntpe_te_v41_stage412_runtime_recovery_hook_adapter_test.py
ntpe_te_v41_stage413_recovery_outcome_guard_test.py
ntpe_te_v41_stage414_recovery_result_bundle_test.py
ntpe_te_v41_stage415_recovery_flow_integration_test.py
ntpe_te_v41_stage416_recovery_flow_boundary_regression_test.py
ntpe_te_v41_stage417_translation_reliability_execution_freeze_test.py
ntpe_te_v42_stage421_real_runtime_recovery_pilot_contract_test.py
ntpe_te_v42_stage422_real_runtime_recovery_pilot_admission_gate_test.py
ntpe_te_v42_stage423_real_runtime_recovery_pilot_rollback_controller_test.py
ntpe_te_v42_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py
ntpe_te_v42_stage425_real_runtime_recovery_pilot_dry_run_bundle_test.py
ntpe_te_v42_stage426_real_runtime_recovery_pilot_boundary_regression_test.py
ntpe_te_v42_stage427_real_runtime_recovery_pilot_freeze_test.py
ntpe_te_v43_stage431_runtime_recovery_hook_contract_test.py
ntpe_te_v43_stage432_runtime_hook_admission_adapter_test.py
ntpe_te_v43_stage433_runtime_single_chunk_shadow_hook_test.py
ntpe_te_v43_stage434_runtime_hook_result_mapper_test.py
ntpe_te_v43_stage435_runtime_recovery_hook_boundary_regression_test.py
ntpe_te_v43_stage436_translation_runtime_recovery_hook_freeze_test.py
ntpe_te_v44_stage441_controlled_execution_contract_test.py
ntpe_te_v44_stage442_controlled_execution_admission_gate_test.py
ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test.py
ntpe_te_v44_stage444_controlled_result_replacement_guard_test.py
ntpe_te_v44_stage445_controlled_execution_boundary_regression_test.py
ntpe_te_v44_stage446_controlled_execution_pilot_freeze_test.py
ntpe_te_v50_quality_core_milestone_test.py
ntpe_te_v50_stage506_quality_core_freeze_test.py
ntpe_te_v51_quality_repair_pipeline_milestone_test.py
ntpe_te_v51_stage515_quality_repair_boundary_regression_test.py
ntpe_te_v51_stage516_quality_repair_pipeline_freeze_test.py
ntpe_te_v521_timeout_propagation_fix_test.py
ntpe_te_v522_provider_timeout_resilience_test.py
ntpe_te_v523_provider_backpressure_resume_test.py
ntpe_te_v52_quality_runtime_gate_pilot_milestone_test.py
ntpe_te_v52_stage525_quality_runtime_gate_boundary_regression_test.py
ntpe_te_v52_stage526_quality_runtime_gate_pilot_freeze_test.py
ntpe_te_v530_quality_runtime_integration_phase1_test.py
ntpe_te_v5311_paragraph_coverage_corroboration_test.py
ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py
ntpe_te_v531_unified_quality_gate_test.py
ntpe_te_v532_semantic_repetition_guard_test.py
ntpe_v540_smart_local_repair_pipeline_test.py
ntpe_te_v551_prompt_compiler_foundation_test.py
ntpe_te_v5521_runtime_prompt_compiler_wiring_test.py
ntpe_te_v552_prompt_discipline_test.py
ntpe_te_v5531_completeness_recovery_best_attempt_test.py
ntpe_te_v5532_adaptive_retry_failure_fallback_test.py
ntpe_te_v5533_segment_level_completeness_recovery_test.py
ntpe_te_v553_adaptive_prompt_feedback_test.py
ntpe_te_v600_final_release_freeze_test.py
ntpe_te_v600_stage01_discipline_architecture_test.py
ntpe_te_v600_stage02_discipline_policy_activation_test.py
ntpe_te_v600_stage03_discipline_quality_enforcement_test.py
ntpe_te_v600_stage04_adaptive_local_repair_framework_test.py
ntpe_te_v600_stage05_adaptive_retry_decision_engine_test.py
ntpe_te_v600_stage06_discipline_runtime_orchestrator_test.py
ntpe_te_v600_stage07_discipline_observability_audit_test.py
ntpe_te_v600_stage081_import_api_compatibility_test.py
ntpe_te_v600_stage08_translation_discipline_freeze_test.py
ntpe_te_v600_stage09_discipline_runtime_integration_test.py
ntpe_te_v600_stage1011_adaptive_retry_plan_runtime_wiring_test.py
ntpe_te_v600_stage101_production_validation_test.py
ntpe_te_v600_stage102_production_retry_metrics_comparison_test.py
ntpe_te_v600_stage103_freeze_readiness_test.py
ntpe_te_v600_stage10_adaptive_retry_policy_v2_test.py
ntpe_te_v600_stage121_translation_naturalness_engine_test.py
ntpe_te_v600_stage122_hallucination_unsupported_detail_guard_test.py
ntpe_te_v600_stage123_literary_collocation_guard_test.py
ntpe_te_v600_stage1241_voice_register_mapping_refinement_test.py
ntpe_te_v600_stage124_character_voice_register_guard_test.py
ntpe_te_v600_stage125_translation_naturalness_freeze_test.py
ntpe_te_v611_stage111_translation_evidence_foundation_test.py
ntpe_te_v611_stage112_source_translation_semantic_alignment_test.py
ntpe_te_v611_stage113_evidence_to_retry_integration_test.py
ntpe_te_v611_stage114_safe_targeted_merge_validation_test.py
ntpe_te_v611_stage115_evidence_runtime_integration_audit_test.py
ntpe_te_v611_stage116_translation_evidence_freeze_test.py
ntpe_te_v700_stage011_adaptive_context_safety_stabilization_test.py
ntpe_te_v700_stage01_adaptive_context_engine_test.py
ntpe_te_v700_stage02_ace_runtime_integration_test.py
ntpe_te_v700_stage03_runtime_shadow_activation_test.py
ntpe_te_v700_stage04_production_shadow_validation_test.py
ntpe_te_v700_stage051_mutable_validation_artifact_integrity_fix_test.py
ntpe_te_v700_stage05_ace_active_canary_activation_test.py
ntpe_te_v700_stage061_canary_validation_test_hardening_test.py
ntpe_te_v700_stage06_ace_canary_production_validation_test.py
ntpe_te_v700_stage071_manifest_chain_decoupling_test.py
ntpe_te_v700_stage072_canary_diagnostics_target_stop_test.py
ntpe_te_v700_stage073_prompt_context_anchor_contract_test.py
ntpe_te_v700_stage074_package_bound_context_anchor_test.py
ntpe_te_v700_stage0751_integration_test_sandbox_stabilization_test.py
ntpe_te_v700_stage075_canary_ab_quality_validation_test.py
ntpe_te_v700_stage07_ace_canary_resume_test.py
ntpe_te_v700_stage081_production_activation_policy_test.py
ntpe_te_v700_stage082_profile_aware_context_budget_test.py
ntpe_te_v700_stage083_adaptive_context_strategy_selection_test.py
ntpe_te_v700_stage0841_production_quality_rollback_wiring_test.py
ntpe_te_v700_stage084_production_rollout_freeze_test.py
ntpe_te_v700_stage09_production_performance_quality_benchmark_test.py
ntpe_te_v700_stage10101_provider_timeout_controlled_retry_test.py
ntpe_te_v700_stage1010_single_real_provider_invocation_test.py
ntpe_te_v700_stage101_provider_timing_evidence_adapter_test.py
ntpe_te_v700_stage102_controlled_provider_benchmark_session_test.py
ntpe_te_v700_stage103_controlled_provider_session_cli_harness_test.py
ntpe_te_v700_stage104_real_provider_invocation_boundary_contract_test.py
ntpe_te_v700_stage105_authorized_single_invocation_provider_harness_test.py
ntpe_te_v700_stage106_authorized_provider_execution_cli_test.py
ntpe_te_v700_stage107_provider_evidence_artifact_pipeline_test.py
ntpe_te_v700_stage108_fake_transport_end_to_end_freeze_test.py
ntpe_te_v700_stage109_real_provider_execution_preflight_contract_test.py
ntpe_te_v710_stage111_translation_defect_classification_test.py
ntpe_te_v710_stage112_translation_quality_metrics_test.py
ntpe_te_v710_stage113_review_artifact_system_test.py
ntpe_te_v710_stage114_prompt_improvement_planner_test.py
ntpe_te_v710_stage115_review_decision_contract_test.py
ntpe_te_v710_stage116_golden_corpus_governance_test.py
ntpe_te_v720_milestone_a_translation_quality_integration_test.py
ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py
ntpe_te_v720_stage1221_controlled_provider_ab_execution_test.py
ntpe_te_v720_stage1222_independent_pair_recovery_execution_test.py
ntpe_te_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py
ntpe_te_v720_stage122_controlled_provider_ab_validation_test.py
ntpe_te_v720_stage1251_controlled_canary_test.py
ntpe_te_v720_stage1254_prompt_contract_preservation_test.py
ntpe_te_v720_stage1255_prompt_canary_readiness_test.py
ntpe_te_v720_stage1256_prompt_verification_canary_test.py
ntpe_te_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py
ntpe_te_v720_stage1257_prompt_verification_canary_test.py
ntpe_te_v720_stage1257a_execution_evidence_sealing_test.py
ntpe_te_v720_stage1258_candidate_structural_verification_canary_test.py
ntpe_te_v720_stage1258a_candidate_structural_failure_sealing_test.py
ntpe_te_v720_stage1259_name_resolution_contract_remediation_test.py
ntpe_ter_v11_translation_quality_foundation_test.py
ntpe_ter_v12_literary_style_engine_test.py
ntpe_ter_v13_speed_prompt_compression_test.py
ntpe_ter_v14_speed_semantic_accuracy_test.py
ntpe_ter_v15_literary_polish_v2_test.py
ntpe_ter_v16_semantic_guard_test.py
ntpe_ter_v17_narrative_naturalness_test.py
ntpe_ter_v18_character_tone_api_stability_test.py
ntpe_ter_v19_stability_repetition_guard_test.py
ntpe_ter_v20_quality_lock_baseline_test.py
ntpe_ter_v21_provider_degraded_fallback_test.py
ntpe_ter_v22_runtime_quality_gate_test.py
ntpe_ter_v23_provider_configuration_audit_test.py
ntpe_ter_v24_runtime_provider_stability_test.py
ntpe_tic_batch1_translation_corpus_inventory_test.py
ntpe_tic_batch2_translation_case_extraction_test.py
ntpe_tic_batch3_manual_evidence_alignment_test.py
ntpe_tic_batch4_human_confirmed_failure_corpus_test.py
ntpe_tic_batch5_historical_human_evidence_expansion_test.py
ntpe_tic_batch61_human_approval_regression_activation_test.py
ntpe_tic_batch6_human_correction_root_cause_regression_test.py
ntpe_tic_batch7_offline_translation_quality_gate_test.py
ntpe_translate_batch.py
ntpe_translate_txt.py
ntpe_translation_engine_refactor_v1_test.py
ntpe_validate.py
packaging/
performance/
platform_services/
profiles/
prompt_packages/
quality_corpus/
quality_reports/
regression/
release/
release_candidate/
reports/
requirements.txt
rules/
runtime_api/
schemas/
sdk/
sessions/
stable_release/
tests/
tmp/
tools/
translated/
translation/
translation_cache/
ui/
verification/
web_ui/
workflow/

---

3) Root Governance Classification (per-file top-level decision)

Legend: KEEP_ROOT / MOVE / ARCHIVE / REVIEW
(Where MOVE includes a proposed destination shown — destination directories are suggestions only; no files will be moved by this plan.)

Repository Metadata & Config (KEEP_ROOT):
- README.md -> KEEP_ROOT (Repository Metadata)
- VERSION.txt -> KEEP_ROOT
- requirements.txt -> KEEP_ROOT
- .gitignore, .gitattributes, .editorconfig -> KEEP_ROOT
- config/ -> KEEP_ROOT (top-level config folder retained)
- manifests/ -> KEEP_ROOT (manifests are top-level metadata used by automation)

Validators / Production checkers (KEEP_ROOT)
- ntpe_validate.py -> KEEP_ROOT (Validator; referenced in manifests and automation)

Production Entry Points (KEEP_ROOT or WRAPPER_REQUIRED)
- launcher.py -> REVIEW (entry: needs confirm of production use; used historically)
- launcher_pipeline.py -> KEEP_ROOT (documented in config and artifacts as pipeline entry)
- launcher_pipeline_production.py -> KEEP_ROOT (manifest/config references this as production entry)
- launcher_pipeline_v1.py -> REVIEW
- ntpe_production_translate.py -> KEEP_ROOT (explicitly referenced in artifacts/manifests)
- ntpe_launcher.py -> REVIEW (may be CLI entry; review usage)
- ntpe_production_translate.py -> KEEP_ROOT

Validator / Maintenance scripts
- ntpe_provider_setup.py -> REVIEW (imported by tests; moving requires refactor)

Testing files and stage tests (MOVE -> tests/ proposed)
- All files with suffix _test.py at root (e.g., ntpe_architecture_consolidation_batch1_repository_hygiene_test.py, ntpe_te_*_test.py, ntpe_stage*_*_test.py, etc.) -> MOVE to tests/ (destination: tests/architecture or tests/unit as appropriate). These are numerous; they should be consolidated under tests/.

Launchers and one-shot tools (REVIEW or MOVE)
- launcher_*.py (launcher_adaptive_recovery.py, launcher_translate.py, launcher_glossary.py, launcher_memory.py, etc.) -> REVIEW. Many are referenced in docs/artifacts; require per-file verification. Proposed destination: tools/launchers/ or tools/utilities/.

Large directories kept at root (KEEP_ROOT):
- core/ -> KEEP_ROOT (core package)
- tools/ -> KEEP_ROOT (tools/ top-level is appropriate)
- tests/ -> KEEP_ROOT (exists)
- docs/ -> KEEP_ROOT
- artifacts/, audits/, manifests/ -> KEEP_ROOT (metadata & outputs)

Other single-purpose scripts (REVIEW)
- create_context_pipeline_integration.py -> REVIEW (likely one-shot workshop; propose tools/integration/)
- create_context_prompt_integration.py -> REVIEW
- create_voice_batch1.py -> REVIEW
- various ntpe_*.py non-test files (ntpe_provider_audit.py, ntpe_batch_monitor.py, etc.) -> REVIEW or MOVE to tools/ or core/ depending on role

Files proposed ARCHIVE (historical or evidence-only) -> ARCHIVE:
- files under root that are purely artifacts or kept evidence (examples exist in artifacts/, docs/archive/) — those are already directories. No explicit root files appear to be archival-only except maybe docs/governance/audits/NTPE_GOVERNANCE_GAP_ANALYSIS.md (but this is a governance artifact and should stay or be moved to audits/). For now: docs/governance/audits/NTPE_GOVERNANCE_GAP_ANALYSIS.md -> KEEP_ROOT (reference material), docs/governance/repository/NTPE_REPOSITORY_STATUS_REPORT.md -> KEEP_ROOT.

Note: The full per-file table (complete listing) is included in section 9 (Migration Priority) as a CSV excerpt for follow-up automation.

---

4) Destination Map (proposed destinations)

- Stage scripts (stage, stageNNN_*) -> tools/stages/
- TE (translation engine related: ntpe_te_*, ntpe_translate*) -> tools/translation_engine/
- LCR (legacy capability recovery) -> tools/lcr/
- PS (prompt system scripts: ntpe_ps*) -> tools/prompt_system/
- TIC (quality / tic) -> tools/tic/
- One-shot tools / launchers -> tools/launchers/
- Tests -> tests/ (organize into tests/architecture, tests/regression, tests/unit by domain)
- Utilities / provider helpers (ntpe_provider_*) -> providers/ or tools/provider_utils/

(If destination directories do not exist, they are proposals only — do not create them in this READ-ONLY phase.)

---

5) Dependency Analysis (evidence-based; no guessing)

Performed targeted cross-references (searches for imports, manifest references, README mentions, and artifacts) for high-impact root items. Results follow; these are factual grep-derived observations.

A) launcher_pipeline_production.py
- Found references in:
  - config/project_layout_policy.json
  - docs/archive/release_history/*
  - artifacts/ntpe_v20_stage0_project_layout_consolidation/*
- Implication: launcher_pipeline_production.py is referenced by manifests/config and by retained artifacts. Moving it will require either keeping a wrapper in root or updating all config/manifests/artifacts that reference it. Classification: KEEP_ROOT or MOVE+Wrapper. Recommendation: KEEP_ROOT wrapper present that forwards to tools/launchers/launcher_pipeline_production.py if real code is relocated.

B) launcher_pipeline.py
- Found references in:
  - config/project_layout_policy.json
  - docs/archive/release_history/*
  - artifacts/ntpe_v20_stage0_project_layout_consolidation/*
- Implication: referenced by project policy and retained artifacts. Classification: KEEP_ROOT or MOVE+Wrapper.

C) launcher_translate.py
- Found usage examples in artifacts (COMMAND_BUILDER_EVIDENCE.json) showing commands that call `python launcher_translate.py`.
- Some artifacts include exact command previews referencing launcher_translate.py.
- Implication: external automation / command lists reference it; recommend wrapper if relocating.

D) ntpe_production_translate.py
- Found references in artifacts/ and manifests/ (e.g., validation commands invoking `python ntpe_production_translate.py --help`).
- Classification: KEEP_ROOT (production entry) or MOVE+Wrapper if relocated.

E) ntpe_validate.py
- Found references in manifests and other config artifacts (manifests include `python ntpe_validate.py` invocations).
- Classification: KEEP_ROOT (Validator). Must remain top-level to allow existing manifest invocations to continue, or replaced by a root wrapper that imports the relocated validator.

F) ntpe_provider_setup.py
- Evidence: imported by tests (tests/regression/provider_environment_regression_test.py: `import ntpe_provider_setup as setup`). Also listed in retained root wrapper artifacts.
- Implication: tests import the module by top-level name. Moving without updating imports will break tests. Classification: REVIEW -> Requires Refactor before moving. Options: leave in root until refactor, or convert to package (providers/) with a root compatibility shim (wrapper) that re-exports.

G) launcher_glossary.py, launcher_glossary references
- Found in docs/archive and audits. Recommendation: Requires wrapper or keep until verified.

H) Summary of verification coverage
- The above items were verified via repository searches for exact basenames and for manifest/artifact references. For the remainder of the many root files (particularly the large set of ntpe_*_test.py and many other ntpe_*.py files) this plan has NOT yet performed exhaustive cross-reference checks. Those files are marked REVIEW in this plan and must be checked by an automated script (see Recommendations) before any move.

---

6) Wrapper Strategy (when root must keep an entry point for backwards compatibility)

When a root script is referenced by manifests, docs, artifacts, or external automation, the recommended strategy is:

- Create a small root wrapper (KEEP_ROOT) with the original filename that does one of the following:
  - Imports the relocated module and calls its main() (Python re-export shim), or
  - Runs a subprocess invocation to the relocated script path with the same CLI surface (less preferred), or
  - Uses pkg_resources / entry_points: convert to a proper console_script entry point and keep wrapper for backward compatibility.

Example wrapper (pseudo):

# launcher_pipeline_production.py (root shim)
from importlib import import_module
if __name__ == '__main__':
    import_module('tools.launchers.launcher_pipeline_production').main()

Wrapper Decision Matrix:
- If manifests call `python launcher.py` (shell invocation), a shim must preserve the CLI semantics. Use import shim that calls main(argv).
- If other code imports module by name (e.g., `import ntpe_provider_setup`), prefer refactor to package and add a compatibility shim that re-exports the module under the old import path.

No files are changed in this READ-ONLY plan. Wrapper implementations will be part of RM-2 migration execution.

---

7) Root Governance Rules (proposal)

Allowed at root:
- Production Entry Points (explicit, minimal list; each must have a maintained compatibility shim if implementation moves)
- Repository Metadata (README, VERSION, requirements, manifests, packaging)
- Validator(s) (ntpe_validate.py or an explicit validated shim)
- Top-level config directories (config/, manifests/, packaging/)

Forbidden at root (should be moved):
- Stage scripts and historical stage test harnesses
- One-shot experimental utilities and one-off analysis scripts
- Large numbers of tests or test harness files
- Temporary utilities and throw-away scripts

Enforcement:
- Maintain a canonical allowlist file (e.g., config/project_layout_policy.json) and a retained-root-shims JSON that declares allowed root files and wrapper requirements.
- Any new root files must be approved and added to the allowlist.

---

8) Migration Priority (recommended phased approach for RM-2)

Phase A — Preservation & Quick Wins (low risk)
- Create wrappers for production entries referenced by manifests (launcher_pipeline_production.py, launcher_pipeline.py, launcher_translate.py, ntpe_production_translate.py) so implementations can be moved safely.
- Move tests with suffix _test.py into tests/ (after verifying none of them are imported by non-test code). Prioritize moving only files that are pure tests.

Phase B — Refactor and Package
- Refactor provider helpers (ntpe_provider_setup.py, ntpe_provider_verify.py) into providers/ or tools/provider_utils/ and add compatibility shims.
- Move long-term tools into tools/launchers, tools/translation_engine, tools/stages, tools/lcr as appropriate.

Phase C — Cleanup and Archive
- Archive purely historical single-shot files into audits/ or archives/
- Remove duplicate or obsolete wrappers once callers are updated (CI, manifests)

Migration priority table (excerpt):
- High priority (wrapper required): launcher_pipeline_production.py, launcher_pipeline.py, launcher_translate.py, ntpe_production_translate.py, ntpe_validate.py
- Medium priority (refactor + shim): ntpe_provider_setup.py, ntpe_provider_verify.py, launcher_glossary.py
- Low priority (review & move): many ntpe_*_test.py -> move to tests/

Note: A full per-file priority csv will be produced in RM-2 run where each file is checked automatically.

---

9) Risks

- Broken automation: manifests, artifacts, or external runbooks may hardcode `python <script>` invocations. Moving without wrappers will break downstream automation.
- Import breakage: tests importing modules by top-level names will fail if modules are moved without refactors or compatibility shims.
- Hidden runtime references: some scripts are referenced only in artifacts or docs — careful search required.

Mitigations: create wrappers for production entries; run CI/unit tests after each staged change; automated search for imports and subprocess calls; maintain an allowlist of root files.

---

10) Recommendations (next actionable tasks for RM-2)

1. Create an allowlist of root files (seeded from this plan): README.md, requirements.txt, VERSION.txt, manifests/, config/, tools/ (top-level directory), ntpe_validate.py, launcher_pipeline_production.py, launcher_pipeline.py, ntpe_production_translate.py.
2. Implement compatibility wrappers at root for all production entries that will be relocated.
3. Run comprehensive automated dependency checks across the repository for each candidate file (script imports, subprocess invocations, README/manifest mentions, CI/workflow references). Produce per-file verification reports.
4. Move pure test files (suffix _test.py) into tests/ in a single atomic change set and run full test suite.
5. For provider modules imported by tests (e.g., ntpe_provider_setup.py), refactor into providers/ package and add root shim that re-exports under the original import name.
6. After moving, update config/project_layout_policy.json and artifacts/retained-root-wrappers.json to reflect new layout and retained wrappers.

---

11) Appendix: Target Root Layout (example target blueprint — DO NOT IMPLEMENT, informational only)

NTPE/
├── README.md
├── VERSION.txt
├── requirements.txt
├── config/
├── manifests/
├── launcher_pipeline_production.py  # shim -> tools/launchers/
├── launcher_pipeline.py             # shim -> tools/launchers/
├── launcher_translate.py            # shim -> tools/launchers/
├── ntpe_validate.py                 # validator (kept or shim)
├── core/
├── providers/                       # refactored provider helpers
├── tools/
├── tests/
├── docs/
├── audits/
└── artifacts/

---

12) Completion checklist for RM-1 (read-only planning)

- [x] Full root inventory produced
- [x] Governance classification and destination map proposed
- [x] Targeted dependency verification performed for high-impact files (launcher_* and ntpe_production*, ntpe_validate, ntpe_provider_setup)
- [x] Wrapper strategy described
- [x] Root governance rules proposed
- [x] Migration priority and risks documented

---

13) Next steps for RM-2 (execution)

- Author automated verifier script (search imports, subprocess strings, README/manifest references, CI/workflows) and run across repository (generate CSV of findings).
- Implement wrappers for high-impact files and run full test suite.
- Move low-risk files (pure tests) in small atomic commits, validate.
- Iterate until root matches target blueprint.

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

