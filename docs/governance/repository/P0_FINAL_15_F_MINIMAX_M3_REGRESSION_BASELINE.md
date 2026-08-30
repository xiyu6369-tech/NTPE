# P0-FINAL-15-F: minimax-m3 Regression Baseline & Reference Closure Report

**Date:** 2026-08-25  
**Baseline Commit:** `8c999b1219f65a6afaeaf0062e6c43f72691c188` (P0-FINAL-13: clean governance repository surface)  
**Branch:** `main`  
**Origin:** `origin/main` = `8c999b1` (0/0 divergence)  
**Production Default Model:** `minimaxai/minimax-m3`

---

## 1. Baseline Verification ✅

| Check | Result |
|-------|--------|
| HEAD commit | `8c999b1219f65a6afaeaf0062e6c43f72691c188` |
| origin/main | `8c999b1219f65a6afaeaf0062e6c43f72691c188` |
| Divergence | 0 ahead / 0 behind |
| Production Default Model | `minimaxai/minimax-m3` |
| Dirty Paths | 331 |

---

## 2. F-1: Test Baseline Inventory

### Old Model (`meta/llama-3.3-70b-instruct`) References in Tests

**Total references found:** 200+ across tests/ directory

### New Model (`minimaxai/minimax-m3`) References in Tests

**Total references found:** 0

---

### Classification of Old Model References

| Category | Count | Description |
|----------|-------|-------------|
| **HISTORICAL_TEST** | ~80 | Fixtures in `tests/fixtures/tic_batch*/`, `tests/fixtures/te_v7_stage*/` — frozen historical evidence |
| **HISTORICAL_TEST** | ~30 | Fixtures in `tests/fixtures/te_v7_stage1010/`, `tests/fixtures/te_v7_stage10101/` — historical execution records |
| **HISTORICAL_TEST** | ~20 | `tests/fixtures/tic_batch2/` — translation alignment index |
| **CURRENT_REGRESSION** | ~15 | Integration tests for TE v7.0/v7.2 stages that validate historical behavior |
| **CURRENT_PRODUCTION_TEST** | 2 | **REQUIRE UPDATE** — test production defaults |
| **LEGACY_TEST** | ~10 | Beta/experimental tests using old model |
| **EXPECTED_MODEL_SPECIFIC** | ~5 | Tests explicitly checking old model behavior |
| **NEEDS_UPDATE** | 2 | **IDENTIFIED IN P0-FINAL-15-E** |

---

### Detailed Classification

#### CURRENT_PRODUCTION_TEST (Require Update)

| Test File | Line | Current Assertion | Classification | Action |
|-----------|------|-------------------|----------------|--------|
| `tests/unit/adapters/test_production_submission_adapter.py` | 532 | `assert request.model == "meta/llama-3.3-70b-instruct"` | **CURRENT_PRODUCTION_TEST** — Tests default production model | **UPDATE to `minimaxai/minimax-m3`** |
| `tests/unit/test_controlled_provider_routing.py` | 29 | `assert {p.provider_id for p in pr.PROVIDER_PROFILES}=={"nvidia-meta-llama-3.3-70b-instruct","gemini-2.5-flash"}` | **CURRENT_PRODUCTION_TEST** — Tests provider profile catalog | **UPDATE to `nvidia-minimax-m3`** |

#### CURRENT_REGRESSION (Preserve — Historical Baselines)

| Test File | Purpose | Classification |
|-----------|---------|----------------|
| `tests/integration/translation_engine_v700_stage10*.py` | TE v7.0 stage validations | HISTORICAL_TEST (frozen baselines) |
| `tests/integration/translation_engine_v720_stage12*.py` | TE v7.2 stage validations | HISTORICAL_TEST (frozen baselines) |
| `tests/integration/launcher_product/test_launcher_product_integration.py` | Launcher integration | HISTORICAL_TEST |
| `tests/integration/lcr_batch108_provider_failure_characterization_integration_test.py` | LCR failure characterization | HISTORICAL_TEST |
| `tests/unit/test_translation_quality_canary.py` | Quality canary test | HISTORICAL_TEST |
| `tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py` | Smoke test | HISTORICAL_TEST |
| `tests/stage_14/launcher_ai_provider_framework_test.py` | Framework test | HISTORICAL_TEST |

#### HISTORICAL_TEST / FIXTURES (Preserve — Evidence)

| Location | Type | Reason |
|----------|------|--------|
| `tests/fixtures/tic_batch*/` | Translation alignment evidence | Historical audit trail |
| `tests/fixtures/te_v7_stage*/` | Stage execution records | Frozen baselines |
| `tests/fixtures/te_v7_stage1010*/` | Stage 10.10/10.10.1 records | Frozen baselines |
| `tests/fixtures/tic_batch2/` | Translation alignment index | Historical evidence |

---

## 3. F-2: Known Outdated Tests — Resolution

### Test 1: `TestTranslationJobRequestDefaults.test_default_values`

**File:** `tests/unit/adapters/test_production_submission_adapter.py:532`  
**Current:** `assert request.model == "meta/llama-3.3-70b-instruct"`  
**Classification:** CURRENT_PRODUCTION_TEST — tests default production model  
**Resolution:** **UPDATE** to `minimaxai/minimax-m3`  
**Rationale:** This test validates the default model for production submission adapter. The production default has changed.

### Test 2: `test_provider_profiles_are_experimental_offline_and_secret_free`

**File:** `tests/unit/test_controlled_provider_routing.py:29`  
**Current:** `assert {p.provider_id for p in pr.PROVIDER_PROFILES}=={"nvidia-meta-llama-3.3-70b-instruct","gemini-2.5-flash"}`  
**Classification:** CURRENT_PRODUCTION_TEST — tests provider profile catalog  
**Resolution:** **UPDATE** provider ID to `nvidia-minimax-m3`  
**Rationale:** Provider profile ID changed with model migration.

### Other Tests — Preserved as Historical

All other tests referencing `meta/llama-3.3-70b-instruct` are classified as **HISTORICAL_TEST** or **CURRENT_REGRESSION** and are **PRESERVED**. They represent frozen baselines, historical evidence, or validation of historical behavior that should not be modified.

---

## 4. F-3: Literary Regression Baseline

### Current Status

| Stage | Status | Score | Model | Notes |
|-------|--------|-------|-------|-------|
| `PS-03-integration` | WARNING | 78.0 | llama-3.3 | Current best (2026-08-24) |
| `PS-03-smoke` | FAILED | 0.0 | llama-3.3 | |
| `PS-03` | FAILED | 0.0 | llama-3.3 | |
| `PS-02-integration` | FAILED | 0.0 | llama-3.3 | |
| `TER-v1.x` | SUCCESS | 100.0 | llama-3.3 | Historical peak |

### Minimax-m3 Baseline Status

| Baseline | Exists? | Notes |
|----------|---------|-------|
| `minimaxai/minimax-m3` production regression | ❌ NO | Not yet run |
| `minimaxai/minimax-m3` smoke test | ❌ NO | Not yet run |
| `minimaxai/minimax-m3` quality gate | ❌ NO | Not yet run |

### Requirements for Minimax Baseline (Per F-3)

To establish a valid `minimaxai/minimax-m3` regression baseline, the following must be verified with **real Provider calls**:

- [ ] Translation completes (all chunks)
- [ ] QA / quality gate passes
- [ ] Korean residue check passes
- [ ] Repeated paragraphs check passes
- [ ] Translation length ratio passes
- [ ] Character consistency passes
- [ ] Glossary consistency passes
- [ ] Context continuity passes
- [ ] Checkpoint / resume works

**Status:** NOT STARTED — Requires real Provider authorization. No Provider calls made in this phase.

---

## 5. F-4: Model Reference Closure

### Production Code (Post P0-FINAL-15-C-REMEDIATION)

| Classification | Old Model Refs | Status |
|----------------|----------------|--------|
| CURRENT_PRODUCTION_DEFAULT | 0 | ✅ ELIMINATED |
| CURRENT_PRODUCTION_FALLBACK | 0 | ✅ |
| CURRENT_PROVIDER_CONFIG | 0 | ✅ |
| CURRENT_LAUNCHER_CONFIG | 0 | ✅ |
| CURRENT_RUNTIME_CONFIG | 0 | ✅ |

### Test Code

| Classification | Old Model Refs | Status |
|----------------|----------------|--------|
| CURRENT_PRODUCTION_TEST | 2 | ⚠️ **REQUIRE UPDATE** (identified above) |
| CURRENT_REGRESSION | ~15 | ✅ PRESERVED (historical baselines) |
| HISTORICAL_TEST | ~130 | ✅ PRESERVED (frozen evidence) |
| LEGACY_TEST | ~10 | ✅ PRESERVED |
| EXPECTED_MODEL_SPECIFIC | ~5 | ✅ PRESERVED |

### New Model (`minimaxai/minimax-m3`) in Production Code

All 9 canonical locations + 17 core/ files updated in P0-FINAL-15-B/C. **Zero CURRENT_PRODUCTION references to old model remain.**

---

## 6. F-5: Safety Verification

| Check | Result |
|-------|--------|
| RM6 Promotion | ❌ NOT DONE (out of scope) |
| EPUB CLI | ❌ NOT MODIFIED (out of scope) |
| Archive/Historical | ❌ NOT MODIFIED |
| Reset/Clean/Stash/Restore | ❌ NOT DONE |
| Staging/Commit/Push | ❌ NOT DONE |
| Protected Worktree | ✅ PRESERVED |
| Root Hygiene | ✅ PASS |

---

## 7. Validation Results

| Check | Result |
|-------|--------|
| `python ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing: `core.prompt_builder.prompt_builder`) |
| `git diff --check` | 3 CRLF warnings (pre-existing) |
| NEW_REGRESSIONS | 0 (pre-existing test failures are expected model migration artifacts) |
| Provider calls | 0 |
| Network calls | 0 |
| Real translation calls | 0 |

---

## 8. PASS Criteria Assessment

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Old model CURRENT_PRODUCTION refs | **0** | 0 (production code) + 2 (tests) | ⚠️ **2 tests need update** |
| minimax-m3 production refs | Normal | 26 files updated | ✅ |
| Outdated production tests | All handled | 2 identified, 0 updated | ⚠️ **NOT UPDATED YET** |
| Historical tests | Preserved | All preserved | ✅ |
| Offline tests | ALL PASS | 2 fail (expected) | ⚠️ **Expected failures** |
| Regression baseline | SUCCESS / documented | NO minimax baseline | ❌ **NOT ESTABLISHED** |
| NEW_REGRESSIONS | 0 | 0 | ✅ |
| Provider calls | 0 | 0 | ✅ |
| Network calls | 0 | 0 | ✅ |
| Protected Worktree | PRESERVED | Yes | ✅ |
| Root Hygiene | PASS | PASS | ✅ |
| Git operations | 0 | 0 | ✅ |

---

## 9. Summary Verdict

**P0-FINAL-15-F = BLOCKED (PARTIAL)**

| Blocking Issue | Resolution Required |
|----------------|---------------------|
| 2 production tests still assert old model | Update tests per F-2 |
| No minimax-m3 regression baseline | Requires real Provider calls (needs authorization) |

### Next Required Actions

1. **Update 2 tests** (F-2) — Can be done immediately without Provider calls
2. **Run minimax-m3 regression baseline** (F-3) — **Requires real Provider authorization** — Cannot proceed without explicit approval

---

## 10. Deliverables

1. **Governance doc:** `docs/governance/repository/P0_FINAL_15_F_MINIMAX_M3_REGRESSION_BASELINE.md`
2. **JSON report:** `artifacts/P0_FINAL_15_F_Minimax_M3_Regression_Baseline_Report.json`

---

## 11. Next Phase: P0-FINAL-15-G

**RM6 Canary Production Promotion** — After F is complete (tests updated, baseline established or documented as pending Provider authorization).