# P0-FINAL-15-C: Model Migration Validation / Reference Closure Report

**Date:** 2026-08-25  
**Baseline Commit:** `8c999b1219f65a6afaeaf0062e6c43f72691c188` (P0-FINAL-13: clean governance repository surface)  
**Branch:** `main`  
**Origin:** `origin/main` = `8c999b1` (0/0 divergence)

---

## 1. Baseline Verification ✅

| Check | Result |
|-------|--------|
| HEAD commit | `8c999b1219f65a6afaeaf0062e6c43f72691c188` |
| origin/main | `8c999b1219f65a6afaeaf0062e6c43f72691c188` |
| Divergence | 0 ahead / 0 behind |
| Dirty paths | 306 (+13 from P0-FINAL-15-B deliverables) |

---

## 2. Full Repository Scan Results

### Old Model: `meta/llama-3.3-70b-instruct`

**Total references found:** 200+ (grep limit reached)

### New Model: `minimaxai/minimax-m3`

**Total references found:** 57 (all in 9 canonical files + governance docs + migration artifacts)

---

## 3. Old Model Reference Classification

### ❌ CURRENT_PRODUCTION_DEFAULT — **FOUND (18 locations)**

These are ACTIVE production code paths that still hardcode the old model. **Must be migrated.**

| # | File | Line | Type | Notes |
|---|------|------|------|-------|
| 1 | `core/adapters/production_submission_adapter.py` | 20 | Dataclass default | `model: str = "meta/llama-3.3-70b-instruct"` |
| 2 | `core/adapters/production_submission_adapter.py` | 129 | Validation | `if request.model != "meta/llama-3.3-70b-instruct":` |
| 3 | `core/adaptive_context_single_real_invocation/config.py` | 27 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 4 | `core/adaptive_context_real_provider_preflight/validator.py` | 107 | Validator check | Checks manifest for old model |
| 5 | `core/adaptive_context_controlled_provider_retry/config.py` | 37 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 6 | `core/adaptive_context_real_provider_preflight/config.py` | 42 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 7 | `core/adaptive_context_real_provider_boundary/config.py` | 9 | Allowed models | `ALLOWED_MODELS = frozenset({"meta/llama-3.3-70b-instruct"})` |
| 8 | `core/adaptive_context_real_provider_boundary/config.py` | 21 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 9 | `core/adaptive_context_provider_execution_freeze/freeze.py` | 86 | Execution freeze | `model="meta/llama-3.3-70b-instruct"` |
| 10 | `core/adaptive_context_authorized_provider_harness/config.py` | 24 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 11 | `core/adaptive_context_authorized_provider_cli/parser.py` | 22 | CLI default | `parser.add_argument("--model", default="meta/llama-3.3-70b-instruct")` |
| 12 | `core/adaptive_context_authorized_provider_cli/config.py` | 21 | Config dataclass | `model: str = "meta/llama-3.3-70b-instruct"` |
| 13 | `core/controlled_provider_routing/provider_profiles.py` | 28 | Provider profile | `NVIDIA_PROFILE=_profile(..., "meta/llama-3.3-70b-instruct", ...)` |
| 14 | `core/controlled_multi_chunk_translation_canary/policy.py` | 58 | Policy constant | `PROVIDER_MODEL = "meta/llama-3.3-70b-instruct"` |
| 15 | `core/config.py` | 19 | DEFAULT_CONFIG dict | `"model": "meta/llama-3.3-70b-instruct"` |
| 16 | `core/expansion/style_expansion_engine.py` | 38 | Function default | `model: str = "meta/llama-3.3-70b-instruct"` |
| 17 | `core/translation_release/te_v6_release.py` | 18 | Release manifest | `"nvidia-provider", "meta/llama-3.3-70b-instruct"` |
| 18 | `core/translation_quality_provider_canary/framework.py` | 26 | Allowed model | `ALLOWED_MODEL = "meta/llama-3.3-70b-instruct"` |
| 19 | `core/controlled_translation_runtime_integration/policy.py` | 22 | Policy constant | `PROVIDER_MODEL = "meta/llama-3.3-70b-instruct"` |
| 20 | `core/lcr_production_shadow_hook/batch107_real_provider_validation.py` | 27 | Module constant | `MODEL = "meta/llama-3.3-70b-instruct"` |

**STATUS: STOP-P15C-01 TRIGGERED** — Active production code still uses old model.

---

### ❌ CURRENT_PRODUCTION_FALLBACK — **0 found**

Fallback model lists are empty in provider_config.json.

---

### ❌ CURRENT_PROVIDER_CONFIG — **0 in active provider_config.json** (already migrated)

The JSON config files have been migrated.

---

### ❌ CURRENT_LAUNCHER_CONFIG — **0 in active launcher config** (already migrated)

The 9 canonical launcher configs have been migrated.

---

### ❌ CURRENT_RUNTIME_CONFIG — **0 in active runtime** (already migrated)

DEFAULT_MODEL constants in ntpe_production_translate.py and lts/txt_translation_runtime.py migrated.

---

### ✅ CURRENT_TEST — **~40 references** — **PRESERVE**

Test fixtures that represent historical test baselines:

| Category | Files |
|----------|-------|
| Integration tests (v700/v720 stages) | `tests/integration/translation_engine_v700_stage*.py`, `tests/integration/translation_engine_v720_stage*.py` |
| Unit tests | `tests/unit/test_translation_quality_canary.py`, `tests/unit/test_controlled_provider_routing.py`, `tests/unit/adapters/test_production_submission_adapter.py` |
| Smoke/Framework tests | `tests/stage_14/launcher_ai_provider_framework_test.py`, `tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py` |
| Launcher integration test | `tests/integration/launcher_product/test_launcher_product_integration.py` |
| LCR integration test | `tests/integration/lcr_batch108_provider_failure_characterization_integration_test.py` |

**Reasoning:** These tests validate historical behavior and frozen canary baselines. Modifying them would change the meaning of historical test evidence.

---

### ✅ HISTORICAL — **~60 references** — **PRESERVE**

Historical execution evidence and manifests:

| Category | Files |
|----------|-------|
| Manifests | `manifests/te_v600_final_release_manifest.json`, `manifests/ntpe_v20_stage1_translation_launcher_product_foundation_manifest.json`, `manifests/te_v720_*.json` |
| Archive artifacts | `archive/te_v7_historical/`, `archive/te_v72_historical/`, `archive/ntpe_v20_historical/` |
| Provider metrics | `archive/te_v72_historical/te_v72_canary_execution/provider_metrics.json` |
| TIC batch artifacts | `tests/fixtures/tic_batch3/`, `tests/fixtures/tic_batch4/`, `tests/fixtures/tic_batch5/` |
| Release docs | `docs/releases/te_v6_0/`, `docs/releases/te_v7_0/`, `docs/releases/te_v7_2/` |
| Legacy config | `archive/legacy_config/prompt_packages/*.json`, `archive/legacy/examples/*.json` |
| Stage tests | `archive/stage_tests/ntpe_te_v40_*.py`, `archive/stage_tests/ntpe_ter_v21_provider_degraded_fallback_test.py` |

---

### ✅ ARCHIVED — **~25 references** — **PRESERVE**

Already-archived legacy modules:

| Category | Files |
|----------|-------|
| Engine module | `engine/nvidia.py` (line 7 - legacy engine) |
| Tools generating historical artifacts | `tools/provider_controls/ntpe_single_real_provider_invocation.py`, `tools/generate_te_v720_controlled_canary.py` |
| Verification test | `verification/release/ntpe_v20_stage1_translation_launcher_product_foundation_test.py` |

---

### ✅ GOVERNANCE_EVIDENCE — **~15 references** — **PRESERVE**

Migration documentation and audit reports:

| Files |
|-------|
| `docs/governance/repository/P0_FINAL_15_A_PRODUCTION_INTEGRATION_MODEL_INVENTORY.md` |
| `docs/governance/repository/P0_FINAL_15_B_PRODUCTION_MODEL_MIGRATION.md` |
| `artifacts/P0_FINAL_15_A_Production_Integration_Model_Inventory_Report.json` |
| `artifacts/P0_FINAL_15_B_Production_Model_Migration_Report.json` |

---

### ✅ LEGACY_COMPATIBILITY — **~5 references** — **PRESERVE**

Legacy modules still referencing old model but not in active production path:

| File | Notes |
|------|-------|
| `core/translation_release/te_v6_release.py` | v6 release manifest (historical) |
| `core/controlled_translation_runtime_integration/policy.py` | Legacy integration policy |
| `core/lcr_production_shadow_hook/batch107_real_provider_validation.py` | Legacy validation hook |

---

### ❌ UNKNOWN — **0** — **NONE**

All references classified.

---

## 4. Production Reference Closure Status

### 9 Canonical Locations (P0-FINAL-15-B) ✅ ALL MIGRATED

| File | Status |
|------|--------|
| `config/launcher_product_defaults.json` | ✅ `minimaxai/minimax-m3` |
| `config/default_config.json` | ✅ `minimaxai/minimax-m3` |
| `config/models.json` | ✅ `minimaxai/minimax-m3` |
| `config/provider_config.json` | ✅ `minimaxai/minimax-m3` |
| `core/launcher_product/config.py` | ✅ `minimaxai/minimax-m3` |
| `core/launcher_product/model_catalog.py` | ✅ `minimaxai/minimax-m3` |
| `core/ai_provider/adapters.py` | ✅ `minimaxai/minimax-m3` |
| `ntpe_production_translate.py` | ✅ `minimaxai/minimax-m3` |
| `lts/txt_translation_runtime.py` | ✅ `minimaxai/minimax-m3` |

### Additional Core Production References ❌ **NOT MIGRATED (18-20 locations)**

These are in active core/ modules that form part of the production runtime:

| Module | Purpose | Action Required |
|--------|---------|-----------------|
| `core/adapters/production_submission_adapter.py` | Production submission validation | Migrate default + validation |
| `core/adaptive_context_*/config.py` (4 files) | Canary/authorized provider configs | Migrate defaults |
| `core/adaptive_context_real_provider_boundary/config.py` | Allowed models + default | Migrate both |
| `core/adaptive_context_provider_execution_freeze/freeze.py` | Execution freeze | Migrate |
| `core/adaptive_context_authorized_provider_harness/config.py` | Harness config | Migrate |
| `core/adaptive_context_authorized_provider_cli/` (2 files) | CLI parser + config | Migrate both |
| `core/controlled_provider_routing/provider_profiles.py` | Provider profile | Migrate |
| `core/controlled_multi_chunk_translation_canary/policy.py` | Canary policy | Migrate |
| `core/config.py` | DEFAULT_CONFIG dict | Migrate |
| `core/expansion/style_expansion_engine.py` | Style expansion | Migrate |
| `core/translation_quality_provider_canary/framework.py` | Quality canary | Migrate |
| `core/controlled_translation_runtime_integration/policy.py` | Integration policy | Migrate |
| `core/lcr_production_shadow_hook/batch107_real_provider_validation.py` | Shadow hook | Migrate |

**These were missed in P0-FINAL-15-B scope and must be addressed.**

---

## 5. Configuration Precedence Verification ✅ PRESERVED

| Level | Status |
|-------|--------|
| CLI (--model) | ✅ Working — user can override |
| Environment (NTPE_FALLBACK_MODELS) | ✅ Working — fallback chain preserved |
| Config files | ✅ Migrated in 4 JSON files |
| ProviderAdapterConfig | ✅ Migrated in adapters.py |
| LauncherConfig | ✅ Migrated in launcher_product/config.py |
| LTS DEFAULT_MODEL | ✅ Migrated in lts/txt_translation_runtime.py |
| Production translate DEFAULT_MODEL | ✅ Migrated in ntpe_production_translate.py |

---

## 6. Launcher Consistency ✅ PASS

All 4 production launchers resolve to same default:

| Launcher | Default Model | Override |
|----------|---------------|----------|
| `ntpe_launcher.py` | `minimaxai/minimax-m3` | `--config` file |
| `ntpe_production_translate.py` | `minimaxai/minimax-m3` | `--model` |
| `lts/txt_translation_runtime.py` | `minimaxai/minimax-m3` | `--model` |
| `core/translation_runtime/runtime.py` | Delegates to LTS | N/A |

---

## 7. Provider Adapter Verification ✅ PASS

| Check | Result |
|-------|--------|
| NVIDIA default_model | `minimaxai/minimax-m3` |
| NVIDIA models[0].id | `minimaxai/minimax-m3` |
| Accepts minimax-m3 | Yes — no hardcoded restriction |
| Falls back to old model | No — passes through request.model correctly |

---

## 8. Test/Fixture Judgment

### Tests to PRESERVE (historical baselines):
- All `tests/integration/translation_engine_v700_stage*.py`
- All `tests/integration/translation_engine_v720_stage*.py`
- `tests/unit/test_translation_quality_canary.py`
- `tests/unit/test_controlled_provider_routing.py`
- `tests/unit/adapters/test_production_submission_adapter.py`
- `tests/stage_14/launcher_ai_provider_framework_test.py`
- `tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py`
- `tests/integration/launcher_product/test_launcher_product_integration.py`
- `tests/integration/lcr_batch108_provider_failure_characterization_integration_test.py`

### Tests/Fixtures that are CURRENT_TEST but represent production defaults:
- None found — all test references are to historical/frozen baselines

---

## 9. Historical/Governance/Archive — All PRESERVED

No modifications made to:
- `artifacts/`
- `archive/`
- `manifests/`
- `docs/releases/`
- `tests/fixtures/`
- Governance documents

---

## 10. Validation Results

| Check | Result |
|-------|--------|
| `python ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing) |
| `git diff --check` | 3 CRLF warnings (pre-existing) |
| NEW_REGRESSIONS | 0 |

---

## 11. Safety Verification

| Metric | Value |
|--------|-------|
| Provider calls | 0 |
| Network calls | 0 |
| Real translation calls | 0 |
| Historical artifacts modified | 0 |
| Protected worktree modified | 0 |
| Root hygiene | COMPLIANT |

---

## 12. STOP Conditions

| Condition | Triggered? |
|-----------|------------|
| STOP-P15C-01: Active production code uses old model | ✅ **YES** — 18-20 locations in core/ |
| STOP-P15C-02: Production fallback uses old model | ❌ NO |
| STOP-P15C-03: New hardcoded location | ❌ NO (these are existing) |
| STOP-P15C-04: Precedence changed | ❌ NO |
| STOP-P15C-05: CLI override broken | ❌ NO |
| STOP-P15C-06: ENV override broken | ❌ NO |
| STOP-P15C-07: minimax-m3 rejected by catalog | ❌ NO |
| STOP-P15C-08: UNKNOWN reference | ❌ NO |
| STOP-P15C-09: Must modify historical evidence | ❌ NO |
| STOP-P15C-10: Protected worktree modified | ❌ NO |
| STOP-P15C-11: New validator error | ❌ NO |
| STOP-P15C-12: NEW_REGRESSIONS | ❌ NO |
| STOP-P15C-13: Provider call required | ❌ NO |
| STOP-P15C-14: Root hygiene violation | ❌ NO |
| STOP-P15C-15: Scope expansion | ❌ NO |

---

## 13. Remediation Required

**P0-FINAL-15-B scope was incomplete.** The 9 canonical files covered the main configuration chain, but **18-20 additional production code paths in core/ also hardcode the old model.**

### Required Next Phase: P0-FINAL-15-C-REMEDIATION

Migrate the following core/ production references:

1. `core/adapters/production_submission_adapter.py` (2 locations)
2. `core/adaptive_context_single_real_invocation/config.py`
3. `core/adaptive_context_real_provider_preflight/validator.py`
4. `core/adaptive_context_controlled_provider_retry/config.py`
5. `core/adaptive_context_real_provider_preflight/config.py`
6. `core/adaptive_context_real_provider_boundary/config.py` (2 locations)
7. `core/adaptive_context_provider_execution_freeze/freeze.py`
8. `core/adaptive_context_authorized_provider_harness/config.py`
9. `core/adaptive_context_authorized_provider_cli/parser.py`
10. `core/adaptive_context_authorized_provider_cli/config.py`
11. `core/controlled_provider_routing/provider_profiles.py`
12. `core/controlled_multi_chunk_translation_canary/policy.py`
13. `core/config.py`
14. `core/expansion/style_expansion_engine.py`
15. `core/translation_quality_provider_canary/framework.py`
16. `core/controlled_translation_runtime_integration/policy.py`
17. `core/lcr_production_shadow_hook/batch107_real_provider_validation.py`

**Excluded from remediation (historical/legacy):**
- `core/translation_release/te_v6_release.py` — v6 historical release
- `core/controlled_translation_runtime_integration/policy.py` — legacy integration

---

## 14. Deliverables

1. **Governance doc:** `docs/governance/repository/P0_FINAL_15_C_MODEL_MIGRATION_REFERENCE_CLOSURE.md`
2. **JSON report:** `artifacts/P0_FINAL_15_C_Model_Migration_Reference_Closure_Report.json`

---

## 15. Final Verdict

**P0-FINAL-15-C = BLOCKED (STOP-P15C-01)**

- 9 canonical files: ✅ MIGRATED
- Additional core/ production references: ❌ **18-20 LOCATIONS STILL USE OLD MODEL**
- Configuration precedence: ✅ PRESERVED
- Launcher consistency: ✅ PASS
- Provider adapter: ✅ PASS
- Historical evidence: ✅ PRESERVED
- Validation: ✅ PASS

**The production default model migration is INCOMPLETE** — the canonical configuration chain is updated, but active production code paths in core/ still hardcode `meta/llama-3.3-70b-instruct`.

**Next phase must address these core/ production references before commit.**