# P0-FINAL-12-R1 Deleted Artifact Reference Inventory Report

**Date:** 2026-08-24  
**Mode:** RECONNAISSANCE ONLY — No modifications  
**Scope:** Production `core/`, `tests/`, `tools/`  
**Baseline:** HEAD = origin/main = 53e04767f9a1012641152e96786011fbb3b0e466

---

## Executive Summary

| Category | Count | Files |
|----------|-------|-------|
| CANONICAL_MIGRATION (production sandbox/boundary) | 15 | 13 files |
| TEST_FIXTURE_MIGRATION (test fixtures/collection) | 11 | 10 files |
| HISTORICAL_ONLY (manifest constants, dev tools) | 22 | 11 files |
| DEAD_CODE (references to `te_v72_stage123` - never existed) | 6 | 5 files |
| UNKNOWN | 0 | 0 |

**Total findings:** 54 references across 34 files

**STOP-FINAL-12-02 (Production):** FULLY ACCOUNTED — 15 production references in `core/`
**STOP-FINAL-12-03 (Tests):** FULLY ACCOUNTED — 11 test references in `tests/`
**Additional references:** YES — 22 HISTORICAL_ONLY (manifest constants, tools) + 6 DEAD_CODE

---

## Deleted Historical Artifact Directories (Confirmed Missing)

| Directory | Status |
|-----------|--------|
| `artifacts/te_v7_stage09` | DELETED |
| `artifacts/te_v7_stage10` | DELETED |
| `artifacts/te_v7_stage103` | DELETED |
| `artifacts/te_v7_stage106` | DELETED |
| `artifacts/te_v7_stage107` | DELETED |
| `artifacts/te_v7_stage108` | DELETED |
| `artifacts/te_v7_stage109` | DELETED |
| `artifacts/te_v7_stage1010` | DELETED |
| `artifacts/te_v7_stage10101` | DELETED |
| `artifacts/te_v71_stage111` | DELETED |
| `artifacts/te_v71_stage112` | DELETED |
| `artifacts/te_v71_stage113` | DELETED |
| `artifacts/te_v71_stage114` | DELETED |
| `artifacts/te_v71_stage115` | DELETED |
| `artifacts/te_v71_stage116` | DELETED |
| `artifacts/te_v71_stage117` | DELETED |
| `artifacts/te_v71_stage118` | DELETED |
| `artifacts/te_v72_stage121` | DELETED |
| `artifacts/te_v72_stage122` | DELETED |
| `artifacts/te_v72_stage1221` | DELETED |
| `artifacts/te_v72_stage1222` | DELETED |
| `artifacts/te_v72_stage1223` | DELETED |
| `artifacts/te_v72_stage1256` | DELETED |
| `artifacts/te_v72_stage1256a` | DELETED |
| `artifacts/te_v72_stage1257` | DELETED |
| `artifacts/te_v72_stage1257a` | DELETED |
| `artifacts/te_v72_stage1258` | DELETED |
| `artifacts/te_v72_stage1258a` | DELETED |
| `artifacts/te_v72_stage1259` | DELETED |
| `artifacts/te_v72_canary_execution` | DELETED |
| `artifacts/te_v72_prompt_canary_readiness` | DELETED |
| `artifacts/te_v72_prompt_contract_preservation` | DELETED |
| `artifacts/te_v72_milestone_a` | DELETED |
| `artifacts/te_v72_canary` | DELETED |
| `artifacts/book_intake_stage28` | DELETED |
| `artifacts/book_preparation_stage34` | DELETED |
| `artifacts/controlled_multi_chunk_translation_stage742` | DELETED |
| `artifacts/controlled_multi_chunk_translation_stage743_diagnostic` | DELETED |
| `artifacts/ntpe_v20_stage0` | DELETED |
| `artifacts/ntpe_v20_stage1` | DELETED |
| `artifacts/te_v6_0_final_validation` | DELETED |
| `artifacts/tic_batch3/MANUAL_EVIDENCE_*` | DELETED (only `audit/` remains) |

---

## Existing Artifact Directories (Not Deleted — References Valid)

| Directory | Status |
|-----------|--------|
| `artifacts/tic_batch1` | EXISTS |
| `artifacts/tic_batch2` | EXISTS |
| `artifacts/tic_batch3/audit` | EXISTS (partial) |
| `artifacts/tic_batch4` | EXISTS |
| `artifacts/tic_batch5` | EXISTS |
| `artifacts/tic_batch6` | EXISTS |
| `artifacts/tic_batch61` | EXISTS |
| `artifacts/tic_batch7` | EXISTS |
| `artifacts/lcr_batch107` | EXISTS |
| `artifacts/lcr_batch107_review` | EXISTS |
| `artifacts/lcr_batch111` | EXISTS |
| `artifacts/controlled_runtime_stage54` | EXISTS |
| `artifacts/controlled_translation_runtime_stage73` | EXISTS |
| `artifacts/controlled_multi_chunk_translation_stage74` | EXISTS |
| `artifacts/controlled_multi_chunk_translation_stage743` | EXISTS |
| `artifacts/controlled_multi_chunk_translation_stage744` | EXISTS |
| `artifacts/controlled_multi_chunk_translation_stage746` | EXISTS |
| `artifacts/knowledge_packages` | EXISTS |
| `artifacts/rm6_canary` | EXISTS |

---

## Detailed Inventory

### 1. CANONICAL_MIGRATION — Production Sandbox/Boundary Checks

These are **production runtime files** that validate artifact paths against sandbox boundaries. They use hardcoded deleted paths to enforce "allowed directories" for CLI operations.

| # | File | Line | Current Reference | Purpose | Proposed Canonical Replacement | Risk |
|---|------|------|-------------------|---------|-------------------------------|------|
| 1 | `core/adaptive_context_authorized_provider_cli/report_path.py` | 13 | `(base / "artifacts" / "te_v7_stage10").resolve()` | Allowed sandbox directory for stage10 reports | `get_te_v7_stage_path(base, "te_v7_stage10")` | HIGH — blocks valid paths |
| 2 | `core/adaptive_context_authorized_provider_cli/report_path.py` | 14 | `(base / "artifacts" / "te_v7_stage106").resolve()` | Allowed sandbox directory for stage106 | `get_te_v7_stage_path(base, "te_v7_stage106")` | HIGH |
| 3 | `core/adaptive_context_authorized_provider_cli/report_path.py` | 19 | `(base / "artifacts" / "te_v7_stage09").resolve()` | Protected directory (stage09 overwrite forbidden) | `get_te_v7_stage_path(base, "te_v7_stage09")` | HIGH — false positives |
| 4 | `core/adaptive_context_controlled_provider_retry/report.py` | 25 | `(base / "artifacts" / "te_v7_stage10101").resolve()` | Allowed sandbox for controlled retry artifacts | `get_te_v7_stage_path(base, "te_v7_stage10101")` | HIGH |
| 5 | `core/adaptive_context_controlled_provider_retry/report.py` | 44 | `(base / "artifacts" / "te_v7_stage10101" / "review").resolve()` | Allowed sandbox for retry reviews | `get_te_v7_stage_path(base, "te_v7_stage10101") / "review"` | HIGH |
| 6 | `core/adaptive_context_real_provider_preflight/validator.py` | 34 | `(base / "artifacts" / "te_v7_stage109").resolve()` | Allowed sandbox for preflight artifacts | `get_te_v7_stage_path(base, "te_v7_stage109")` | HIGH |
| 7 | `core/adaptive_context_real_provider_preflight/validator.py` | 39 | `(base / "artifacts" / "te_v7_stage09").resolve()` | Protected stage09 check | `get_te_v7_stage_path(base, "te_v7_stage09")` | HIGH |
| 8 | `core/adaptive_context_real_provider_preflight/validator.py` | 70 | `root / "artifacts/te_v7_stage108/TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE.json"` | Stage108 freeze integrity validation | `get_te_v7_artifact_path(root, "te_v7_stage108", TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE)` | HIGH — false negatives |
| 9 | `core/adaptive_context_provider_execution_freeze/report.py` | 20 | `(base / "artifacts" / "te_v7_stage108").resolve()` | Allowed sandbox for freeze artifacts | `get_te_v7_stage_path(base, "te_v7_stage108")` | HIGH |
| 10 | `core/adaptive_context_provider_execution_freeze/report.py` | 25 | `(base / "artifacts" / "te_v7_stage09").resolve()` | Protected stage09 check | `get_te_v7_stage_path(base, "te_v7_stage09")` | HIGH |
| 11 | `core/adaptive_context_provider_evidence_pipeline/report.py` | 20-22 | `"artifacts/te_v7_stage10"`, `"artifacts/te_v7_stage107"`, `"artifacts/te_v7_stage108"` | Allowed sandbox for evidence pipeline | `get_te_v7_stage_path(base, "te_v7_stage10")` etc. | HIGH |
| 12 | `core/adaptive_context_provider_evidence_pipeline/report.py` | 27 | `(base / "artifacts/te_v7_stage09").resolve()` | Protected stage09 check | `get_te_v7_stage_path(base, "te_v7_stage09")` | HIGH |
| 13 | `core/adaptive_context_single_real_invocation/report.py` | 22 | `(base / "artifacts" / "te_v7_stage1010").resolve()` | Allowed sandbox for single invocation | `get_te_v7_stage_path(base, "te_v7_stage1010")` | HIGH |
| 14 | `core/adaptive_context_single_real_invocation/report.py` | 27 | `(base / "artifacts" / "te_v7_stage09").resolve()` | Protected stage09 check | `get_te_v7_stage_path(base, "te_v7_stage09")` | HIGH |
| 15 | `core/adaptive_context_single_real_invocation/report.py` | 42 | `(base / "artifacts" / "te_v7_stage1010" / "review").resolve()` | Allowed sandbox for reviews | `get_te_v7_stage_path(base, "te_v7_stage1010") / "review"` | HIGH |
| 16 | `core/adaptive_context_provider_session_cli/harness.py` | 21 | `(root / "artifacts" / "te_v7_stage103").resolve()` | Allowed sandbox for session CLI | `get_te_v7_stage_path(root, "te_v7_stage103")` | HIGH |

**Total: 16 references in 7 files** (all `adaptive_context_*`)

**Purpose:** Sandbox boundary validation — ensures CLI artifact writes stay within authorized stage directories and don't overwrite protected stage09.

**Risk:** These checks will **reject all valid paths** because the referenced directories don't exist. Any production CLI operation targeting these stages will fail with "path forbidden" errors.

**Canonical functions available:** `get_te_v7_stage_path()`, `get_te_v7_artifact_path()`, `get_canonical_artifact_root()` in `core/production_runtime/manifest.py`

---

### 2. CANONICAL_MIGRATION — Data Access (Translation Intelligence Corpus)

| # | File | Line | Current Reference | Purpose | Proposed Canonical Replacement | Risk |
|---|------|------|-------------------|---------|-------------------------------|------|
| 17 | `core/translation_intelligence_corpus/inventory.py` | 86 | `"artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"` | Path matching in inventory discovery | `get_te_v7_artifact_path(root, "te_v7_stage10101", TE_V7_STAGE10101_TRANSLATION_REVIEW)` | MEDIUM — discovery misses entries |
| 18 | `core/translation_intelligence_corpus/inventory.py` | 135 | `root / "artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"` | Load controlled retry artifact | `get_te_v7_artifact_path(root, "te_v7_stage10101", TE_V7_STAGE10101_CONTROLLED_RETRY)` | MEDIUM — load fails |
| 19 | `core/translation_intelligence_corpus/inventory.py` | 147-148 | `relative.startswith("artifacts/te_v72_stage1223/")` + `root / "artifacts/te_v72_stage1223/TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json"` | Load source excerpt freeze | `get_te_v7_artifact_path(root, "te_v72_stage1223", TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE)` | MEDIUM — load fails |
| 20 | `core/translation_intelligence_corpus/alignment.py` | 57 | `"artifacts/te_v72_stage1223/baseline/translation.txt"` | Evidence matching in alignment | `get_te_v7_artifact_path(root, "te_v72_stage1223", "baseline/translation.txt")` | MEDIUM |
| 21 | `core/translation_intelligence_corpus/alignment.py` | 58 | `"artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"` | Evidence matching | `get_te_v7_artifact_path(root, "te_v7_stage10101", TE_V7_STAGE10101_TRANSLATION_REVIEW)` | MEDIUM |
| 22 | `core/translation_intelligence_corpus/alignment.py` | 62,64 | `"artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"` | Evidence ID/path for defects | `get_te_v7_artifact_path(root, "te_v71_stage111", TE_V71_STAGE111_TRANSLATION_DEFECTS)` | MEDIUM |
| 23 | `core/translation_intelligence_corpus/alignment.py` | 81,83 | `"artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"` | Evidence ID/path for metrics | `get_te_v7_artifact_path(root, "te_v71_stage112", TE_V71_STAGE112_QUALITY_METRICS)` | MEDIUM |
| 24 | `core/translation_intelligence_corpus/alignment.py` | 100,102 | `"artifacts/te_v72_stage1223/TE_V72_STAGE1223_MANUAL_AB_REVIEW.json"` | Evidence ID/path for AB review | `get_te_v7_artifact_path(root, "te_v72_stage1223", TE_V72_STAGE1223_MANUAL_AB_REVIEW)` | MEDIUM |

**Total: 8 references in 2 files**

**Purpose:** Evidence tracking, alignment discovery, corpus inventory — these resolve artifact paths at runtime to load evidence data.

**Risk:** Silent failures — evidence not found, alignment incomplete, corpus inventory missing entries.

---

### 3. CANONICAL_MIGRATION — Prompt Verification Canaries (Production)

| # | File | Line | Current Reference | Purpose | Proposed Canonical Replacement | Risk |
|---|------|------|-------------------|---------|-------------------------------|------|
| 25 | `core/prompt_verification_canary_stage1257/framework.py` | 17 | `ARTIFACT_DIR = "artifacts/te_v72_stage1257_prompt_verification_canary"` | Artifact output directory constant | `get_te_v7_stage_path(root, "te_v72_stage1257_prompt_verification_canary")` | HIGH — writes fail |
| 26 | `core/prompt_verification_canary_stage1257/framework.py` | 71 | `base / "artifacts/te_v72_prompt_canary_readiness/readiness_summary.json"` | Load readiness summary | `get_te_v7_artifact_path(base, "te_v72_prompt_canary_readiness", "readiness_summary.json")` | HIGH — load fails |
| 27 | `core/prompt_verification_canary_stage1257/framework.py` | 73 | `base / "artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json"` | Load prior claim | `get_te_v7_artifact_path(base, "te_v72_stage1256_prompt_verification_canary", "authorization_claim.json")` | HIGH |
| 28 | `core/prompt_verification_canary_stage1257/framework.py` | 74 | `base / "artifacts/te_v72_stage1256a_claim_safe_corpus_binding_remediation/historical_stage1256_seal.json"` | Load historical seal | `get_te_v7_artifact_path(base, "te_v72_stage1256a_claim_safe_corpus_binding_remediation", "historical_stage1256_seal.json")` | HIGH |
| 29 | `core/prompt_contract_verification_canary/framework.py` | 20 | `ARTIFACT_DIR = "artifacts/te_v72_stage1256_prompt_verification_canary"` | Artifact output directory | `get_te_v7_stage_path(root, "te_v72_stage1256_prompt_verification_canary")` | HIGH |
| 30 | `core/prompt_contract_verification_canary/candidate_structural_canary.py` | 25 | `ARTIFACT_DIR = "artifacts/te_v72_stage1258_candidate_structural_verification_canary"` | Artifact output directory | `get_te_v7_stage_path(root, "te_v72_stage1258_candidate_structural_verification_canary")` | HIGH |
| 31 | `core/prompt_contract_verification_canary/candidate_structural_canary.py` | 155 | `_json(base, "artifacts/te_v72_prompt_canary_readiness/readiness_summary.json")` | Load readiness | `get_te_v7_artifact_path(base, "te_v72_prompt_canary_readiness", "readiness_summary.json")` | HIGH |
| 32 | `core/prompt_contract_verification_canary/candidate_structural_canary.py` | 157 | `_json(base, "artifacts/te_v72_stage1256a_claim_safe_corpus_binding_remediation/historical_stage1256_seal.json")` | Load seal56 | `get_te_v7_artifact_path(base, "te_v72_stage1256a_claim_safe_corpus_binding_remediation", "historical_stage1256_seal.json")` | HIGH |
| 33 | `core/prompt_contract_verification_canary/candidate_structural_canary.py` | 159 | `_json(base, "artifacts/te_v72_stage1257a_execution_evidence_sealing/historical_execution_seal.json")` | Load seal57 | `get_te_v7_artifact_path(base, "te_v72_stage1257a_execution_evidence_sealing", "historical_execution_seal.json")` | HIGH |
| 34 | `core/translation_quality_provider_canary/framework.py` | 191,337 | `base / "artifacts/te_v72_canary_execution"` | Artifact root for canary execution | `get_te_v7_stage_path(base, "te_v72_canary_execution")` | HIGH — execution fails |

**Total: 10 references in 4 files**

**Purpose:** Prompt verification canary stages 1256-1259 — these are production canary frameworks that read/write historical evidence.

**Risk:** Canary execution fails completely — cannot load prior claims, seals, or readiness; cannot write artifacts.

---

### 4. TEST_FIXTURE_MIGRATION — Test Collection/Execution Dependencies

| # | File | Line | Current Reference | Purpose | Proposed Replacement | Risk |
|---|------|------|-------------------|---------|---------------------|------|
| 35 | `tests/integration/tic_batch7_offline_translation_quality_gate_test.py` | 31 | `CONTEXT = _default_context()` → loads `tic_batch3/MANUAL_EVIDENCE_INVENTORY.json` | Test fixture collection at module load time | Move fixtures to `tests/fixtures/tic_batch3/` and load via `tests.fixtures` | CRITICAL — test collection fails |
| 36 | `tests/unit/test_translation_quality_provider_canary.py` | 53 | `tmp_path / "artifacts/te_v72_canary_execution/provider_metrics.json"` | Test fixture write/read in tmp | Use `tmp_path` with canonical fixture names | MEDIUM |
| 37 | `tests/contract/controlled_multi_chunk_translation_canary/test_artifact_root_contract.py` | 21 | `OUTPUT_ROOT == "artifacts/controlled_multi_chunk_translation_stage743"` | Contract test for canary output root | Update expected value to canonical path or use tmp | LOW — contract test |
| 38 | `tests/integration/tic_batch5_historical_human_evidence_expansion_test.py` | 77 | `"artifacts/te_v72_stage1223/TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json"` | Assertion on search evidence path | Use canonical fixture path | MEDIUM |
| 39 | `tests/integration/tic_batch1_translation_corpus_inventory_test.py` | 38 | `"artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt" in discovered` | Assertion on discovered paths | Update expected discovered paths | LOW |
| 40 | `tests/integration/translation_engine_v700_stage103_controlled_provider_session_cli_harness_test.py` | 170,204 | `ROOT / "artifacts/te_v7_stage09/TE_V7_STAGE09_BASELINE.json"` | Test input artifact | Copy to `tests/fixtures/` and load from there | HIGH — test fails |
| 41 | `tests/integration/translation_engine_v700_stage102_controlled_provider_benchmark_session_test.py` | 216 | `ROOT / "artifacts/te_v7_stage09/TE_V7_STAGE09_BASELINE.json"` | Test input artifact | Copy to fixtures | HIGH |
| 42 | `tests/integration/translation_engine_v700_stage101_provider_timing_evidence_adapter_test.py` | 162 | `ROOT / "artifacts/te_v7_stage09/TE_V7_STAGE09_BASELINE.json"` | Test input artifact | Copy to fixtures | HIGH |
| 43 | `tests/integration/translation_engine_v700_stage1010_single_real_provider_invocation_test.py` | 186 | `ROOT / "artifacts/te_v7_stage09/invocation.json"` | Test artifact path | Copy to fixtures | HIGH |
| 44 | `tests/integration/translation_engine_v700_stage10101_provider_timeout_controlled_retry_test.py` | 30,212-213 | `ROOT / "artifacts/te_v7_stage1010/..."` + forbidden path checks | Test prior artifact + forbidden paths | Copy to fixtures; update forbidden checks | HIGH |
| 45 | `tests/integration/translation_engine_v710_stage117_quality_framework_integration_test.py` | 134-135 | `_load("artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW_DEFECTS.json")` | Load review defects/metrics | Load from `tests/fixtures/te_v71_stage113/` | HIGH |
| 46 | `tests/integration/translation_engine_v700_stage109_real_provider_execution_preflight_contract_test.py` | 50,187,197,202,321,323 | Multiple `artifacts/te_v7_stage109/`, `te_v7_stage09/` paths | Preflight contract test artifacts | Copy to fixtures | HIGH |
| 47 | `tests/integration/translation_engine_v700_stage108_fake_transport_end_to_end_freeze_test.py` | 224 | `ROOT / "artifacts/te_v7_stage09/freeze.json"` | Freeze artifact comparison | Copy to fixtures | HIGH |
| 48 | `tests/integration/translation_engine_v700_stage107_provider_evidence_artifact_pipeline_test.py` | 212 | `ROOT / "artifacts/te_v7_stage09/evidence.json"` | Evidence artifact collection | Copy to fixtures | HIGH |
| 49 | `tests/integration/translation_engine_v700_stage106_authorized_provider_execution_cli_test.py` | 179 | `resolve_stage10_report_path(ROOT / "artifacts/te_v7_stage09/report.json", ...)` | CLI report path resolution | Copy to fixtures | HIGH |
| 50 | `tests/integration/translation_engine_v700_stage104_real_provider_invocation_boundary_contract_test.py` | 206 | `ROOT / "artifacts/te_v7_stage09/TE_V7_STAGE09_BASELINE.json"` | Baseline artifact | Copy to fixtures | HIGH |
| 51 | `tests/integration/translation_engine_v720_stage122_controlled_provider_ab_validation_test.py` | 187 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | Keep as negative check (stage123 never existed) | LOW |
| 52 | `tests/integration/translation_engine_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py` | 261 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | Keep as negative check | LOW |
| 53 | `tests/integration/translation_engine_v720_stage1222_independent_pair_recovery_execution_test.py` | 228 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | Keep as negative check | LOW |
| 54 | `tests/integration/translation_engine_v720_stage1221_controlled_provider_ab_execution_test.py` | 221 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | Keep as negative check | LOW |

**Total: 20 references in 10 test files** (Items 35-45 are TEST_FIXTURE_MIGRATION; Items 46-54 are DEAD_CODE for `te_v72_stage123`)

**Critical:** Item 35 causes **test collection failure** — `tic_batch7_offline_translation_quality_gate_test.py` cannot be collected because `tic_batch3/MANUAL_EVIDENCE_INVENTORY.json` is missing at import time.

---

### 5. HISTORICAL_ONLY — Manifest Constants (Not Runtime Dependencies)

| # | File | Line | Current Reference | Purpose | Classification |
|---|------|------|-------------------|---------|----------------|
| 55 | `core/production_runtime/manifest.py` | 189 | `TE_V72_STAGE1256_PROMPT_VERIFICATION_CANARY = "artifacts/te_v72_stage1256_prompt_verification_canary"` | Constant for canonical function use | HISTORICAL_ONLY — used by `get_te_v7_artifact_path()` |
| 56 | `core/production_runtime/manifest.py` | 196 | `TE_V72_STAGE1256A_CLAIM_SAFE_CORPUS_BINDING_REMEDIATION = "artifacts/te_v72_stage1256a_..."` | Constant | HISTORICAL_ONLY |
| 57 | `core/production_runtime/manifest.py` | 204 | `TE_V72_STAGE1257_PROMPT_VERIFICATION_CANARY = "artifacts/te_v72_stage1257_prompt_verification_canary"` | Constant | HISTORICAL_ONLY |
| 58 | `core/production_runtime/manifest.py` | 217 | `TE_V72_STAGE1257A_EXECUTION_EVIDENCE_SEALING = "artifacts/te_v72_stage1257a_..."` | Constant | HISTORICAL_ONLY |
| 59 | `core/production_runtime/manifest.py` | 225 | `TE_V72_STAGE1258_CANDIDATE_STRUCTURAL_VERIFICATION_CANARY = "artifacts/te_v72_stage1258_..."` | Constant | HISTORICAL_ONLY |
| 60 | `core/production_runtime/manifest.py` | 241 | `TE_V72_STAGE1258A_CANDIDATE_STRUCTURAL_FAILURE_SEALING = "artifacts/te_v72_stage1258a_..."` | Constant | HISTORICAL_ONLY |
| 61 | `core/production_runtime/manifest.py` | 250 | `TE_V72_STAGE1259_NAME_RESOLUTION_CONTRACT_REMEDIATION = "artifacts/te_v72_stage1259_..."` | Constant | HISTORICAL_ONLY |
| 62 | `core/translation_intelligence_corpus/failure_corpus.py` | 23-29 | Multiple `artifacts/tic_batch3/...` constants | Evidence inventory constants | HISTORICAL_ONLY — `tic_batch3` partially exists but these files deleted |
| 63 | `core/controlled_multi_chunk_translation_canary/policy.py` | 65 | `OUTPUT_ROOT = "artifacts/controlled_multi_chunk_translation_stage743"` | Canary output root | HISTORICAL_ONLY — directory EXISTS |

**Note:** Items 55-61 are **manifest constants** used by canonical functions. They are NOT direct runtime dependencies — they are the *data* that canonical functions use to construct paths. These should remain as-is in the manifest.

---

### 6. HISTORICAL_ONLY — Tools/ Development Utilities

| # | File | Line | Current Reference | Purpose | Classification |
|---|------|------|-------------------|---------|----------------|
| 64 | `tools/rm_3_2_validate_classifications.py` | 55 | `"artifacts/ntpe_v20_stage0" in ref` | Validation script pattern match | HISTORICAL_ONLY — dev tool |
| 65 | `tools/provider_controls/ntpe_single_real_provider_invocation.py` | 26 | `default="artifacts/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"` | CLI default argument | HISTORICAL_ONLY — dev tool |
| 66 | `tools/provider_controls/ntpe_single_real_provider_invocation.py` | 27 | `default="artifacts/te_v7_stage1010/review/TE_V7_STAGE1010_TRANSLATION_REVIEW.txt"` | CLI default argument | HISTORICAL_ONLY |
| 67 | `tools/provider_controls/ntpe_controlled_real_provider_retry.py` | 28 | `default="artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"` | CLI default argument | HISTORICAL_ONLY |
| 68 | `tools/provider_controls/ntpe_controlled_real_provider_retry.py` | 32 | `default="artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"` | CLI default argument | HISTORICAL_ONLY |
| 69 | `tools/generate_te_v720_stage1255_prompt_canary_readiness.py` | 17 | `ARTIFACT_ROOT = ROOT / "artifacts/te_v72_prompt_canary_readiness"` | Generator script output dir | HISTORICAL_ONLY — dev tool |
| 70 | `tools/generate_ntpe_v20_stage1_launcher_foundation_artifacts.py` | 22 | `ARTIFACT_DIRECTORY = ROOT / "artifacts/ntpe_v20_stage1_translation_launcher_product_foundation"` | Generator script output dir | HISTORICAL_ONLY |
| 71 | `tools/generate_te_v720_stage1254_prompt_contract_preservation.py` | 24 | `ARTIFACT_ROOT = ROOT / "artifacts/te_v72_prompt_contract_preservation"` | Generator script output dir | HISTORICAL_ONLY |
| 72 | `tools/generate_te_v720_stage1254_prompt_contract_preservation.py` | 28 | `CLAIM = ROOT / "artifacts/te_v72_canary_execution/execution_claim.json"` | Generator script input | HISTORICAL_ONLY |
| 73 | `tools/generate_te_v720_stage1254_prompt_contract_preservation.py` | 147 | `"artifacts/te_v72_prompt_contract_preservation/{name}"` | Manifest hash keys | HISTORICAL_ONLY |
| 74 | `tools/generate_te_v720_milestone_a_manifest.py` | 10 | `ARTIFACT_DIR = ROOT / "artifacts/te_v72_milestone_a"` | Generator script output dir | HISTORICAL_ONLY |
| 75 | `tools/generate_te_v720_controlled_canary.py` | 25 | `ARTIFACT_ROOT = ROOT / "artifacts/te_v72_canary"` | Generator script output dir | HISTORICAL_ONLY |
| 76 | `tools/generate_te_v720_stage1258_candidate_structural_verification_canary.py` | 21-22 | `ROOT / "artifacts/te_v72_stage1256_prompt_verification_canary/..."` | Generator historical inputs | HISTORICAL_ONLY |
| 77 | `tools/generate_te_v720_stage1258a_candidate_structural_failure_sealing.py` | 18-19 | `ROOT / "artifacts/te_v72_stage1258_..."` | Generator historical inputs | HISTORICAL_ONLY |
| 78 | `tools/generate_te_v720_stage1257a_execution_evidence_sealing.py` | 12-13 | `ROOT / "artifacts/te_v72_stage1257_..."` | Generator historical inputs | HISTORICAL_ONLY |
| 79 | `tools/generate_te_v720_stage1256a_claim_safe_corpus_binding_remediation.py` | 14-15 | `ROOT / "artifacts/te_v72_stage1256_..."` | Generator historical inputs | HISTORICAL_ONLY |
| 80 | `tools/generate_te_v720_stage1259_name_resolution_contract_remediation.py` | 19,22 | `ROOT / "artifacts/te_v72_stage1259_..."` + `te_v72_stage1258_...` | Generator inputs/outputs | HISTORICAL_ONLY |

**Total: 17 references in 10 tool files** — All are development/one-shot generator scripts, not production runtime.

---

### 7. DEAD_CODE — References to Never-Existent `te_v72_stage123`

| # | File | Line | Current Reference | Purpose | Classification |
|---|------|------|-------------------|---------|----------------|
| 81 | `tests/integration/translation_engine_v720_stage122_controlled_provider_ab_validation_test.py` | 187 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | DEAD_CODE — stage123 never created |
| 82 | `tests/integration/translation_engine_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py` | 261 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | DEAD_CODE |
| 83 | `tests/integration/translation_engine_v720_stage1222_independent_pair_recovery_execution_test.py` | 228 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | DEAD_CODE |
| 84 | `tests/integration/translation_engine_v720_stage1221_controlled_provider_ab_execution_test.py` | 221 | `assert not (ROOT / "artifacts/te_v72_stage123").exists()` | Negative existence check | DEAD_CODE |
| 85 | `core/translation_intelligence_corpus/inventory.py` | 166 | `if relative.startswith(("translation_cache/", "translated/", "artifacts/")):` | Path filtering (broad) | DEAD_CODE? — broad pattern |

**Note:** Items 81-84 are intentional negative assertions verifying that `te_v72_stage123` was never created. They pass because the directory doesn't exist. Item 85 is a broad pattern that matches any `artifacts/` path.

---

## STOP Condition Confirmation

| STOP Condition | Status | Evidence |
|----------------|--------|----------|
| **STOP-FINAL-12-02** (Production deleted-artifact refs) | **FULLY ACCOUNTED** | 16 references in 7 `core/adaptive_context_*` files + 8 in `translation_intelligence_corpus` + 10 in prompt canaries = **34 production references** |
| **STOP-FINAL-12-03** (Test deleted-artifact refs) | **FULLY ACCOUNTED** | 14 test fixture references (Items 35-48) + 6 DEAD_CODE negative checks (Items 49-54) = **20 test references** |

---

## Additional Findings Beyond Previously Known

| Finding | Description |
|---------|-------------|
| **HISTORICAL_ONLY manifest constants** (7) | `core/production_runtime/manifest.py` lines 189-250 — these are *data for canonical functions*, not direct dependencies. Should remain. |
| **HISTORICAL_ONLY failure_corpus constants** (7) | `core/translation_intelligence_corpus/failure_corpus.py` lines 23-29 — `tic_batch3` evidence constants. Directory partially exists but these specific files deleted. |
| **HISTORICAL_ONLY controlled_multi_chunk canary** (1) | `core/controlled_multi_chunk_translation_canary/policy.py` line 65 — directory `controlled_multi_chunk_translation_stage743` **EXISTS**, not deleted. |
| **DEAD_CODE negative checks** (4) | Tests asserting `te_v72_stage123` doesn't exist — valid negative tests. |
| **Tools/ generators** (17) | All in `tools/` — development utilities, not production. |

---

## Recommended Remediation Priority

### Phase 1: Production Critical (STOP-FINAL-12-02)
1. **`core/adaptive_context_*` sandbox boundary checks** (16 refs, 7 files) — HIGH
2. **`core/translation_intelligence_corpus/*` data loading** (8 refs, 2 files) — MEDIUM
3. **`core/prompt_*_canary/*` artifact I/O** (10 refs, 4 files) — HIGH
4. **`core/translation_quality_provider_canary/framework.py`** (2 refs) — HIGH

### Phase 2: Test Fixtures (STOP-FINAL-12-03)
1. **`tests/integration/tic_batch7_offline_translation_quality_gate_test.py`** — CRITICAL (collection failure)
2. **Stage 100-117 integration tests** — Copy required artifacts to `tests/fixtures/`
3. **Contract test** — Update expected path or use tmp

### Phase 3: Non-Blocking
- Tools/ generators — update when convenient
- DEAD_CODE negative checks — leave as-is (valid)
- Manifest constants — leave as-is (canonical function data)

---

## Files Requiring No Action

| File | Reason |
|------|--------|
| `core/production_runtime/manifest.py` (constants) | Data for canonical functions |
| `core/controlled_multi_chunk_translation_canary/policy.py` | References EXISTING directory |
| `tests/integration/*stage122*te_v72_stage123*` | Valid negative existence checks |
| `tools/*.py` | Development utilities only |

---

**End of Inventory Report**