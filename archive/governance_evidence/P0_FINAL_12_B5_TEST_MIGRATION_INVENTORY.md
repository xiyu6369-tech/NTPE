# P0-FINAL-12-B5 Test Migration Inventory

**Baseline:** HEAD=origin/main=2bedad8
**Date:** 2026-08-23

---

## Inventory Summary

| Category | Test Files | Artifact Dependencies | Migration Priority |
|---|---|---|---|
| TE v7.1 Quality Framework (Stage 111-118) | 13 | artifacts/te_v71_stage111-118/* | B5-A / B5-B |
| TE v7.2 Stage 121-125 Canary | 12 | artifacts/te_v72_stage121-125*, te_v72_canary/* | B5-A / B5-B |
| TIC Batch 1-7 | 11 | artifacts/tic_batch1-7/*, tic_batch61/* | B5-A / B5-C |
| LCR Batch 107 | 2 | artifacts/tic_batch2/*, lcr_batch107_review/* | B5-A |
| Controlled Multi-Chunk Canary | 2 | artifacts/controlled_multi_chunk_translation_stage743-746/* | B5-A |
| Prompt Verification Canary | 3 | artifacts/te_v72_stage1256-1258/* | B5-B |

**Total:** 43 test files, 20+ unique artifact dependencies

---

## Detailed Inventory

### 1. TE v7.1 Quality Framework Tests (13 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 1 | tests/unit/public_api/test_quality_review_api.py | - | artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json | evidence | manifests/te_v710_stage113_review_artifact_system_manifest.json | fixture | LOW |
| 2 | tests/unit/public_api/test_quality_assessment_api.py | - | artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json | evidence | manifests/te_v710_stage111_translation_defect_classification_manifest.json | fixture | LOW |
| 3 | tests/unit/public_api/test_corpus_api.py | - | artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json | evidence | manifests/te_v710_stage116_golden_corpus_governance_manifest.json | fixture | LOW |
| 4 | tests/integration/architecture_consolidation_batch4_quality_api_consolidation_test.py | - | All 6 TE v7.1 artifacts | evidence | All 6 manifests | fixture | MEDIUM |
| 5 | tests/integration/translation_engine_v710_stage111_translation_defect_classification_test.py | test_artifact_integrity_and_boundaries, test_artifact_contains_exact_fixed_ids, test_artifact_has_no_full_review_copy, test_defect_artifact_tamper_fails | artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json | freeze evidence | manifest + core.translation_quality_defects.verify_defect_artifact | canonical import | MEDIUM |
| 6 | tests/integration/translation_engine_v710_stage112_translation_quality_metrics_test.py | - | artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json | freeze evidence | manifest | fixture | LOW |
| 7 | tests/integration/translation_engine_v710_stage113_review_artifact_system_test.py | - | artifacts/te_v71_stage113/* | freeze evidence | manifest | fixture | LOW |
| 8 | tests/integration/translation_engine_v710_stage114_prompt_improvement_planner_test.py | - | artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json | freeze evidence | manifest | fixture | LOW |
| 9 | tests/integration/translation_engine_v710_stage115_review_decision_contract_test.py | - | artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json | freeze evidence | manifest | fixture | LOW |
| 10 | tests/integration/translation_engine_v710_stage116_golden_corpus_governance_test.py | - | artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json | freeze evidence | manifest | fixture | LOW |
| 11 | tests/integration/translation_engine_v710_stage117_quality_framework_integration_test.py | - | artifacts/te_v71_stage117/TE_V71_STAGE117_QUALITY_FRAMEWORK_INTEGRATION.json | freeze evidence | manifest | fixture | LOW |
| 12 | tests/integration/translation_engine_v710_stage118_translation_quality_framework_freeze_test.py | test_freeze_identity_and_status, test_every_frozen_inventory_path_exists, test_all_prior_stage_manifest_hashes_are_frozen, test_every_file_in_prior_manifests_matches_sha256, test_stage117_integration_artifact_is_frozen, test_golden_corpus_hash_and_content_are_frozen, test_no_plan_was_applied, test_no_decision_was_applied, test_no_corpus_approval_was_created, test_framework_boundary_is_frozen_and_inactive, test_freeze_does_not_claim_quality_improvement, test_freeze_adds_no_new_core_module, test_release_document_declares_future_compatibility_boundary, test_freeze_manifest_is_deterministic_and_complete, test_freeze_manifest_anchors_prior_manifests, test_freeze_manifest_files_match, test_validation_summary_is_fully_stable, test_root_and_integration_test_inventory_covers_all_stages, test_required_historical_regressions_are_frozen | artifacts/te_v71_stage118/TE_V71_STAGE118_TRANSLATION_QUALITY_FRAMEWORK_FREEZE.json | freeze contract | manifest + core constants | canonical import | HIGH |
| 13 | tests/performance/quality_api_facade_benchmark.py | - | All 6 TE v7.1 artifacts | benchmark data | manifests | generated temp data | LOW |

---

### 2. TE v7.2 Stage 121-125 Canary Tests (12 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 14 | tests/unit/test_translation_quality_provider_canary.py | - | artifacts/te_v72_canary_execution/provider_metrics.json | canary evidence | generated temp data | tmp_path fixture | LOW |
| 15 | tests/unit/test_stage1258_candidate_structural_verification_canary.py | test_historical_claim_is_immutable_and_not_replayable | artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json, artifacts/te_v72_stage1257_prompt_verification_canary/authorization_claim.json | historical claim | manifests/te_v720_stage1256_prompt_verification_canary_manifest.json, te_v720_stage1257_prompt_verification_canary_manifest.json | fixture | MEDIUM |
| 16 | tests/unit/test_stage1257_prompt_verification_canary.py | - | artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json | historical claim | manifest | fixture | MEDIUM |
| 17 | tests/unit/test_stage1256a_claim_safe_corpus_binding.py | test_historical_claim_is_immutable_and_not_replayable | artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json | historical claim | manifest | fixture | MEDIUM |
| 18 | tests/integration/translation_engine_v720_stage121_evidence_based_prompt_quality_candidate_test.py | - | artifacts/te_v72_stage121/TE_V72_STAGE121_PROVIDER_EXECUTION_PACKAGE.json, TE_V72_STAGE121_EVIDENCE_BASED_PROMPT_QUALITY_CANDIDATE.json | canary evidence | manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json | fixture | MEDIUM |
| 19 | tests/integration/translation_engine_v720_stage122_controlled_provider_ab_validation_test.py | test_expected_artifact_exists_and_is_in_package | artifacts/te_v72_stage122/* | freeze evidence | manifest + core constants | canonical import | MEDIUM |
| 20 | tests/integration/translation_engine_v720_stage1221_controlled_provider_ab_execution_test.py | - | artifacts/te_v72_stage1221/* | freeze evidence | manifest | fixture | MEDIUM |
| 21 | tests/integration/translation_engine_v720_stage1222_independent_pair_recovery_execution_test.py | - | artifacts/te_v72_stage1222/* | freeze evidence | manifest | fixture | MEDIUM |
| 22 | tests/integration/translation_engine_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py | - | artifacts/te_v72_stage1223/TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json | freeze contract | manifests/te_v720_stage1223_minimal_excerpt_ab_quality_validation_manifest.json | canonical import | HIGH |
| 23 | tests/integration/translation_engine_v720_stage1251_controlled_canary_test.py | - | artifacts/te_v72_canary/* | canary evidence | manifest | fixture | LOW |
| 24 | tests/integration/translation_engine_v720_stage1252_authorized_provider_canary_test.py | - | artifacts/te_v72_canary_execution/* | canary evidence | manifest | fixture | LOW |
| 25 | tests/integration/translation_engine_v720_stage1254_prompt_contract_preservation_test.py | - | artifacts/te_v72_canary_execution/execution_claim.json | canary evidence | manifest | fixture | LOW |

---

### 3. TIC Batch 1-7 Tests (11 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 26 | tests/integration/tic_batch1_translation_corpus_inventory_test.py | - | artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json, STATISTICS, MANIFEST | corpus inventory | manifests/tic_batch1_translation_corpus_inventory_manifest.json | canonical import | MEDIUM |
| 27 | tests/integration/tic_batch2_translation_case_extraction_test.py | test_inventory_to_case_extraction_uses_frozen_batch1_inputs, test_translation_cases_and_timeout_execution_evidence_are_separated, test_case_metadata_and_sha_preservation_are_complete, test_translation_text_is_preserved_without_retranslation, test_chunk_order_number_and_offsets_are_preserved, test_metadata_search_index_covers_every_case, test_case_statistics_recompute_exactly, test_artifact_and_root_manifests_match_sha256, test_extraction_is_deterministic, test_extraction_does_not_modify_historical_translations | artifacts/tic_batch2/TRANSLATION_CASES.json, INDEX, STATISTICS, ARTIFACT_MANIFEST | corpus extraction | manifests/tic_batch2_translation_case_extraction_manifest.json + core TIC API | canonical import | HIGH |
| 28 | tests/integration/tic_batch3_manual_evidence_alignment_test.py | - | artifacts/tic_batch2/CASES, tic_batch3/INVENTORY, LINKS, ALIGNMENTS, STATISTICS, INDEX, MANIFEST | corpus alignment | manifests/tic_batch3_manual_evidence_alignment_manifest.json + core TIC API | canonical import | HIGH |
| 29 | tests/integration/tic_batch4_human_confirmed_failure_corpus_test.py | - | artifacts/tic_batch4/HUMAN_CONFIRMED_FAILURE_CORPUS.json, EXCLUDED, STATISTICS, INDEX, MANIFEST | failure corpus | manifests/tic_batch4_human_confirmed_failure_corpus_manifest.json + core TIC API | canonical import | HIGH |
| 30 | tests/integration/tic_batch5_historical_human_evidence_expansion_test.py | - | artifacts/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION.json, CORPUS_V2, UNRESOLVED, REPORT, STATISTICS, INDEX, EXCELLENCE | evidence expansion | manifests/tic_batch5_historical_human_evidence_expansion_manifest.json + core TIC API | canonical import | HIGH |
| 31 | tests/integration/tic_batch6_human_correction_root_cause_regression_test.py | - | artifacts/tic_batch6/HUMAN_CORRECTION_RECORDS.json, ROOT_CAUSE_RECORDS.json, REGRESSIONS, VALIDATION, STATISTICS, INDEX | regression test | manifests/tic_batch6_human_correction_root_cause_regression_manifest.json + core TIC API | canonical import | HIGH |
| 32 | tests/integration/tic_batch61_human_approval_regression_activation_test.py | - | artifacts/tic_batch61/HUMAN_APPROVAL_RECORDS.json, CORRECTIONS_V2, ACTIVE, VALIDATION, STATISTICS, INDEX | approval test | manifests/tic_batch61_human_approval_regression_activation_manifest.json + core TIC API | canonical import | HIGH |
| 33 | tests/integration/tic_batch7_offline_translation_quality_gate_test.py | - | artifacts/tic_batch7/VALIDATION, STATISTICS, INDEX, GATE, FIXTURES, PERFORMANCE | quality gate | manifests/tic_batch7_offline_translation_quality_gate_manifest.json + core TIC API | canonical import | HIGH |
| 34 | tests/integration/lcr_batch5_dual_pass_translation_integration_test.py | - | artifacts/tic_batch7/OFFLINE_QUALITY_GATE_FIXTURES.json | quality gate fixtures | tests/fixtures/lcr_batch9/tic_cases.json | fixture | MEDIUM |
| 35 | tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py | test_tic_human_approved_and_historical_bad_cases_use_real_offline_gate | artifacts/tic_batch7/OFFLINE_QUALITY_GATE_FIXTURES.json | quality gate fixtures | tests/fixtures/lcr_batch9/tic_cases.json | fixture | MEDIUM |
| 36 | tests/performance/tic_batch7_offline_quality_gate_benchmark.py | - | artifacts/tic_batch7/OFFLINE_QUALITY_GATE_PERFORMANCE.json | benchmark output | tmp_path | generated temp data | LOW |

---

### 4. LCR Batch 107 Tests (2 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 37 | tests/unit/test_lcr_batch107_real_provider_validation.py | sandbox(), execute() | artifacts/tic_batch2/TRANSLATION_CASES.json | test data copy | tmp_path + core TIC API | tmp_path fixture | MEDIUM |
| 38 | tests/integration/lcr_batch107_pre_execution_package_integration_test.py | - | artifacts/tic_batch2/TRANSLATION_CASES.json | test data copy | tmp_path + core TIC API | tmp_path fixture | MEDIUM |

---

### 5. Controlled Multi-Chunk Translation Canary Tests (2 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 39 | tests/contract/controlled_multi_chunk_translation_canary/test_artifact_root_contract.py | test_default_and_authorized_override_are_exact_contract_values, test_prior_canary_roots_contract, test_stage746_not_in_prior_canary_roots | artifacts/controlled_multi_chunk_translation_stage743-746/* | contract constants | core.controlled_multi_chunk_translation_canary.policy | canonical import (already done) | LOW |
| 40 | tests/unit/controlled_multi_chunk_translation_canary/test_dialogue_normalization_stage745.py | - | artifacts/controlled_multi_chunk_translation_stage744/ | historical path | core constant | canonical import | LOW |

---

### 6. Prompt Verification Canary Tests (3 files)

| # | Test File | Test Functions | Deleted Artifact | Type | Canonical Source | Migration Method | Risk |
|---|---|---|---|---|---|---|---|
| 41 | tests/unit/test_stage1256a_claim_safe_corpus_binding.py | test_historical_claim_is_immutable_and_not_replayable | artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json | historical claim | manifest | fixture | MEDIUM |
| 42 | tests/unit/test_stage1257_prompt_verification_canary.py | - | artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json | historical claim | manifest | fixture | MEDIUM |
| 43 | tests/unit/test_stage1258_candidate_structural_verification_canary.py | test_historical_claim_is_immutable_and_not_replayable | artifacts/te_v72_stage1256/authorization_claim.json, artifacts/te_v72_stage1257/authorization_claim.json | historical claim | manifests | fixture | MEDIUM |

---

## Migration Strategy by Category

### B5-A: Direct Artifact Path References
Files with simple `Path("artifacts/...")` or `ROOT / "artifacts/..."` references.
- Replace with canonical manifest paths or core API calls
- Use `tmp_path` fixture for writable test data

### B5-B: Historical Evidence Tests
Tests that verify historical evidence content.
- Convert to use canonical manifests + deterministic fixtures
- Tests in `tests/fixtures/` or generated via `tmp_path`

### B5-C: Manifest/Hash Tests
Tests that verify artifact identity via SHA256.
- Redirect to canonical manifests in `manifests/`
- Core modules now expose verification functions

### B5-D: Corpus/TIC Tests
Tests for Translation Intelligence Corpus.
- Use `core.translation_intelligence_corpus` API
- Fixtures in `tests/fixtures/lcr_batch*/` or `tests/fixtures/te_v72_canary/`

### B5-E: Runtime/Adaptive Context Tests
Tests for adaptive context integration.
- Use core adaptive_context modules directly
- No artifact dependencies needed

---

## Canonical Source Mapping

| Deleted Artifact | Canonical Source | Location |
|---|---|---|
| artifacts/te_v71_stage111/* | te_v710_stage111_translation_defect_classification_manifest.json | manifests/ |
| artifacts/te_v71_stage112/* | te_v710_stage112_translation_quality_metrics_manifest.json | manifests/ |
| artifacts/te_v71_stage113/* | te_v710_stage113_review_artifact_system_manifest.json | manifests/ |
| artifacts/te_v71_stage114/* | te_v710_stage114_prompt_improvement_planner_manifest.json | manifests/ |
| artifacts/te_v71_stage115/* | te_v710_stage115_review_decision_contract_manifest.json | manifests/ |
| artifacts/te_v71_stage116/* | te_v710_stage116_golden_corpus_governance_manifest.json | manifests/ |
| artifacts/te_v71_stage117/* | te_v710_stage117_quality_framework_integration_manifest.json | manifests/ |
| artifacts/te_v71_stage118/* | te_v710_stage118_translation_quality_framework_freeze_manifest.json | manifests/ |
| artifacts/te_v72_stage121/* | te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json | manifests/ |
| artifacts/te_v72_stage122/* | te_v720_stage122_controlled_provider_ab_validation_manifest.json | manifests/ |
| artifacts/te_v72_stage1221/* | te_v720_stage1221_controlled_provider_ab_execution_manifest.json | manifests/ |
| artifacts/te_v72_stage1222/* | te_v720_stage1222_independent_pair_recovery_execution_manifest.json | manifests/ |
| artifacts/te_v72_stage1223/* | te_v720_stage1223_minimal_excerpt_ab_quality_validation_manifest.json | manifests/ |
| artifacts/te_v72_canary/* | te_v720_controlled_canary_manifest.json, te_v720_authorized_provider_canary_manifest.json | manifests/ |
| artifacts/tic_batch1/* | tic_batch1_translation_corpus_inventory_manifest.json | manifests/ |
| artifacts/tic_batch2/* | tic_batch2_translation_case_extraction_manifest.json | manifests/ |
| artifacts/tic_batch3/* | tic_batch3_manual_evidence_alignment_manifest.json | manifests/ |
| artifacts/tic_batch4/* | tic_batch4_human_confirmed_failure_corpus_manifest.json | manifests/ |
| artifacts/tic_batch5/* | tic_batch5_historical_human_evidence_expansion_manifest.json | manifests/ |
| artifacts/tic_batch6/* | tic_batch6_human_correction_root_cause_regression_manifest.json | manifests/ |
| artifacts/tic_batch61/* | tic_batch61_human_approval_regression_activation_manifest.json | manifests/ |
| artifacts/tic_batch7/* | tic_batch7_offline_translation_quality_gate_manifest.json | manifests/ |
| artifacts/controlled_multi_chunk_translation_stage743-746/* | core.controlled_multi_chunk_translation_canary.policy | core/ |
| artifacts/te_v72_stage1256-1258/* | te_v720_stage1256/1257/1258_*_manifest.json | manifests/ |

---

## Frozen Contract Impact

| Test File | Frozen Contract | Impact |
|---|---|---|
| translation_engine_v710_stage118_translation_quality_framework_freeze_test.py | TE-v7.1 Stage 118 Freeze | YES - tests the freeze contract itself |
| translation_engine_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py | TE-v7.2 Stage 1223 Source Excerpt Freeze | YES - tests the freeze contract itself |
| tic_batch2_translation_case_extraction_test.py | TIC Batch 2 extraction | YES - verifies deterministic extraction |
| tic_batch4_human_confirmed_failure_corpus_test.py | TIC Batch 4 failure corpus | YES - verifies corpus integrity |
| test_stage1256a_claim_safe_corpus_binding.py | Prompt Contract Verification Canary | YES - tests claim immutability |

**Action:** These tests must maintain semantic equivalence. Migration must use canonical manifests, not restore artifacts.

---

## STOP Conditions Monitoring

| Condition | Status | Notes |
|---|---|---|
| STOP-B5-01: New production dependency | Monitoring | |
| STOP-B5-02: Frozen contract modification | Monitoring | |
| STOP-B5-03: Artifact restoration required | Monitoring | |
| STOP-B5-04: Production code modification | Monitoring | |
| STOP-B5-05: Protected Worktree modified | Monitoring | |
| STOP-B5-06: Root filesystem artifact | Monitoring | |
| STOP-B5-07: New series regression failure | Monitoring | |
| STOP-B5-08: Semantic equivalence failure | Monitoring | |
| STOP-B5-09: UNKNOWN dependency | Monitoring | |
| STOP-B5-10: 207 deleted artifacts count change | Monitoring | |

---

## Next Steps

1. Begin migration with B5-A (Direct Artifact Path References)
2. Progress through B5-B, B5-C, B5-D, B5-E
3. Run validation gates after each category
4. Update inventory with migration status
5. Create final implementation report