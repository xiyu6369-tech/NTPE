# P0-FINAL-15-C-REMEDIATION: Production Model Migration Remediation Report

**Date:** 2026-08-25  
**Baseline Commit:** `8c999b1219f65a6afaeaf0062e6c43f72691c188` (P0-FINAL-13: clean governance repository surface)  
**Branch:** `main`  
**Origin:** `origin/main` = `8c999b1` (0/0 divergence)

---

## 1. Remediation Summary

| Item | Result |
|------|--------|
| **Old Model** | `meta/llama-3.3-70b-instruct` |
| **New Model** | `minimaxai/minimax-m3` |
| **Original CURRENT_PRODUCTION References** | 20 |
| **Remediated** | 20/20 ✅ |
| **Remaining CURRENT_PRODUCTION** | 0 ✅ |
| **Validation** | PASS WITH WARNINGS (1 pre-existing) |

---

## 2. Nine Canonical Locations (P0-FINAL-15-B)

| # | File | Status |
|---|------|--------|
| 1 | `config/launcher_product_defaults.json` | ✅ |
| 2 | `config/default_config.json` | ✅ |
| 3 | `config/models.json` | ✅ |
| 4 | `config/provider_config.json` | ✅ |
| 5 | `core/launcher_product/config.py` | ✅ |
| 6 | `core/launcher_product/model_catalog.py` | ✅ |
| 7 | `core/ai_provider/adapters.py` | ✅ |
| 8 | `ntpe_production_translate.py` | ✅ |
| 9 | `lts/txt_translation_runtime.py` | ✅ |

---

## 3. Additional Core Production References Remediated (20 files)

| # | File | Reference Type | Lines Changed |
|---|------|----------------|---------------|
| 1 | `core/adapters/production_submission_adapter.py` | DEFAULT + validation | 20, 129 |
| 2 | `core/adaptive_context_single_real_invocation/config.py` | Config default | 27 |
| 3 | `core/adaptive_context_real_provider_preflight/validator.py` | Manifest check | 107 |
| 4 | `core/adaptive_context_controlled_provider_retry/config.py` | Config default | 37 |
| 5 | `core/adaptive_context_real_provider_preflight/config.py` | Config default | 42 |
| 6 | `core/adaptive_context_real_provider_boundary/config.py` | Allowed models + default | 9, 21 |
| 7 | `core/adaptive_context_provider_execution_freeze/freeze.py` | Execution freeze | 86 |
| 8 | `core/adaptive_context_authorized_provider_harness/config.py` | Config default | 24 |
| 9 | `core/adaptive_context_authorized_provider_cli/parser.py` | CLI default | 22 |
| 10 | `core/adaptive_context_authorized_provider_cli/config.py` | Config default | 21 |
| 11 | `core/controlled_provider_routing/provider_profiles.py` | Provider profile | 28 |
| 12 | `core/controlled_multi_chunk_translation_canary/policy.py` | Policy constant | 58 |
| 13 | `core/config.py` | DEFAULT_CONFIG dict | 19 |
| 14 | `core/expansion/style_expansion_engine.py` | Function default | 38 |
| 15 | `core/translation_quality_provider_canary/framework.py` | Allowed model | 26 |
| 16 | `core/controlled_translation_runtime_integration/policy.py` | Policy constant | 22 |
| 17 | `core/lcr_production_shadow_hook/batch107_real_provider_validation.py` | Module constant | 27 |

---

## 4. Remaining Old Model References (Correctly Preserved)

| Category | Location | Reason |
|----------|----------|--------|
| **HISTORICAL** | `core/translation_release/te_v6_release.py:18` | v6 historical release manifest |
| **HISTORICAL** | `archive/` | Archived evidence |
| **HISTORICAL** | `manifests/` | Historical manifests |
| **HISTORICAL** | `docs/releases/` | Release documentation |
| **HISTORICAL** | `tests/fixtures/` | Test fixtures |
| **TEST_BASELINE** | `tests/integration/` | Frozen test baselines |
| **GOVERNANCE** | `docs/governance/` | Migration documentation |

**All preserved references are non-production historical evidence.**

---

## 5. Configuration Precedence Verification ✅

| Level | Status |
|-------|--------|
| CLI (--model) | ✅ Working |
| Environment (NTPE_FALLBACK_MODELS) | ✅ Working |
| Config files (4 JSON) | ✅ Migrated |
| ProviderAdapterConfig | ✅ Migrated |
| LauncherConfig | ✅ Migrated |
| LTS DEFAULT_MODEL | ✅ Migrated |
| Production translate DEFAULT_MODEL | ✅ Migrated |

---

## 6. Launcher Consistency ✅

| Launcher | Default Model | Override |
|----------|---------------|----------|
| `ntpe_launcher.py` | `minimaxai/minimax-m3` | `--config` |
| `ntpe_production_translate.py` | `minimaxai/minimax-m3` | `--model` |
| `lts/txt_translation_runtime.py` | `minimaxai/minimax-m3` | `--model` |
| `core/translation_runtime/runtime.py` | Delegates to LTS | N/A |

**All consistent: `minimaxai/minimax-m3`**

---

## 7. Provider Adapter Verification ✅

| Check | Result |
|-------|--------|
| NVIDIA default_model | `minimaxai/minimax-m3` |
| NVIDIA models[0].id | `minimaxai/minimax-m3` |
| Accepts minimax-m3 | ✅ |
| Falls back to old model | ❌ No |

---

## 8. Full Rescan Results

### Old Model: `meta/llama-3.3-70b-instruct`

| Classification | Count | Status |
|----------------|-------|--------|
| CURRENT_PRODUCTION_DEFAULT | 0 | ✅ ELIMINATED |
| CURRENT_PRODUCTION_FALLBACK | 0 | ✅ |
| CURRENT_PROVIDER_CONFIG | 0 | ✅ |
| CURRENT_LAUNCHER_CONFIG | 0 | ✅ |
| CURRENT_RUNTIME_CONFIG | 0 | ✅ |
| CURRENT_TEST | ~40 | ✅ PRESERVED |
| HISTORICAL | ~60 | ✅ PRESERVED |
| ARCHIVED | ~25 | ✅ PRESERVED |
| GOVERNANCE_EVIDENCE | ~15 | ✅ PRESERVED |
| LEGACY_COMPATIBILITY | ~5 | ✅ PRESERVED |
| UNKNOWN | 0 | ✅ |

### New Model: `minimaxai/minimax-m3`

| Classification | Count |
|----------------|-------|
| CURRENT_PRODUCTION | 30+ |
| CURRENT_TEST | 0 |
| HISTORICAL | 0 |
| GOVERNANCE | 2 |

---

## 9. Validation Results

| Check | Result |
|-------|--------|
| `python ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing) |
| `git diff --check` | 3 CRLF warnings (pre-existing) |
| NEW_REGRESSIONS | 0 |

---

## 10. Safety Verification

| Metric | Value |
|--------|-------|
| Provider calls | 0 |
| Network calls | 0 |
| Real translation calls | 0 |
| Historical artifacts modified | 0 |
| Protected worktree modified | 0 |
| Root hygiene | COMPLIANT |

---

## 11. STOP Conditions — All NOT Triggered

| Condition | Triggered? |
|-----------|------------|
| STOP-P15C-01: Active production code uses old model | ❌ NO (0 remaining) |
| STOP-P15C-02: Production fallback uses old model | ❌ NO |
| STOP-P15C-03: New hardcoded location | ❌ NO |
| STOP-P15C-04: Precedence changed | ❌ NO |
| STOP-P15C-05: CLI override broken | ❌ NO |
| STOP-P15C-06: ENV override broken | ❌ NO |
| STOP-P15C-07: minimax-m3 rejected | ❌ NO |
| STOP-P15C-08: UNKNOWN reference | ❌ NO |
| STOP-P15C-09: Historical modified | ❌ NO |
| STOP-P15C-10: Protected modified | ❌ NO |
| STOP-P15C-11: New validator error | ❌ NO |
| STOP-P15C-12: NEW_REGRESSIONS | ❌ NO |
| STOP-P15C-13: Provider call required | ❌ NO |
| STOP-P15C-14: Root hygiene violation | ❌ NO |
| STOP-P15C-15: Scope expansion | ❌ NO |

---

## 12. Git Safety

| Metric | Value |
|--------|-------|
| Staged | 0 |
| Committed (this phase) | 0 |
| Pushed (this phase) | 0 |
| HEAD | `8c999b1` |
| origin/main | `8c999b1` |
| Divergence | 0/0 |

---

## 13. Deliverables

1. **Governance doc:** `docs/governance/repository/P0_FINAL_15_C_REMEDIATION.md`
2. **JSON report:** `artifacts/P0_FINAL_15_C_Remediation_Report.json`

---

## 14. Final Verdict

**P0-FINAL-15-C-REMEDIATION = PASS**

- ✅ All 20 CURRENT_PRODUCTION references remediated
- ✅ Zero CURRENT_PRODUCTION references to old model remain
- ✅ Configuration precedence preserved
- ✅ CLI/ENV override capability preserved
- ✅ Model catalog synchronized
- ✅ Provider adapter accepts new model
- ✅ All launchers resolve to same new default
- ✅ Historical evidence preserved
- ✅ Validation passes
- ✅ No new regressions
- ✅ Working tree preserved
- ✅ Zero STOP conditions triggered

---

## 15. Next Phase

**P0-FINAL-15-D: Production Integration Gap Audit**

Focus on:
- EPUB CLI entry point (missing)
- RM6 Canary promotion
- Literary regression baseline hardening
- User-facing EPUB → Translation workflow