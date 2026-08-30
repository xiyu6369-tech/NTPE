# P0-FINAL-15-B: Production Model Migration Report

**Date:** 2026-08-25  
**Baseline Commit:** `8c999b1219f65a6afaeaf0062e6c43f72691c188` (P0-FINAL-13: clean governance repository surface)  
**Branch:** `main`  
**Origin:** `origin/main` = `8c999b1` (0/0 divergence)

---

## 1. Migration Summary

| Item | Before | After |
|------|--------|-------|
| **Old Model** | `meta/llama-3.3-70b-instruct` | — |
| **New Model** | — | `minimaxai/minimax-m3` |
| **Canonical Files Modified** | 9 | 9 |
| **Validation** | PASS | PASS |

---

## 2. Nine Canonical Production Default Locations Updated

| # | File | Change | Type |
|---|------|--------|------|
| 1 | `config/launcher_product_defaults.json` | `"model_id": "meta/llama-3.3-70b-instruct"` → `"minimaxai/minimax-m3"` | JSON config |
| 2 | `config/default_config.json` | `"model": "meta/llama-3.3-70b-instruct"` → `"minimaxai/minimax-m3"` | JSON config |
| 3 | `config/models.json` | `"default": "meta/llama-3.3-70b-instruct"` + `"models": ["meta/llama-3.3-70b-instruct"]` → both `"minimaxai/minimax-m3"` | JSON config |
| 4 | `config/provider_config.json` | `"default_model": "meta/llama-3.3-70b-instruct"` → `"minimaxai/minimax-m3"` | JSON config |
| 5 | `core/launcher_product/config.py` | `_BASE_CONFIG["model_id"]` default → `"minimaxai/minimax-m3"` | Python dict |
| 6 | `core/launcher_product/model_catalog.py` | `ModelDefinition` entry → `model_id="minimaxai/minimax-m3"`, `display_name="Minimax M3"` | Python code |
| 7 | `core/ai_provider/adapters.py` | `ProviderAdapterConfig.default_model` + `models[0].id` → `"minimaxai/minimax-m3"` | Python code |
| 8 | `ntpe_production_translate.py` | `DEFAULT_MODEL` constant → `"minimaxai/minimax-m3"` | Python constant |
| 9 | `lts/txt_translation_runtime.py` | `DEFAULT_MODEL` constant → `"minimaxai/minimax-m3"` | Python constant |

---

## 3. Configuration Precedence Preserved

The model resolution chain remains intact:

```
1. CLI argument (--model)                    ✅ WORKING
2. Environment variable (NTPE_FALLBACK_MODELS) ✅ WORKING  
3. Config files (launcher_product_defaults.json → default_config.json → models.json → provider_config.json) ✅ UPDATED
4. ProviderAdapterConfig.default_model       ✅ UPDATED
5. LauncherConfig._BASE_CONFIG               ✅ UPDATED
6. TxtTranslationOptions.DEFAULT_MODEL       ✅ UPDATED
7. ntpe_production_translate.py DEFAULT_MODEL ✅ UPDATED
```

**Verified:** User can still override via `--model` CLI argument. Environment fallback chain preserved.

---

## 4. Production Effective Default Verification

All 4 production launchers resolve to the same new default:

| Launcher | Effective Default Model | Verified |
|----------|------------------------|----------|
| `ntpe_launcher.py` | `minimaxai/minimax-m3` | ✅ |
| `ntpe_production_translate.py` | `minimaxai/minimax-m3` | ✅ |
| `lts/txt_translation_runtime.py` | `minimaxai/minimax-m3` | ✅ |
| `core/translation_runtime/runtime.py` (delegates to LTS) | `minimaxai/minimax-m3` | ✅ |

**Configuration consistency:** PASS

---

## 5. Model Catalog Updated

| Model | Provider | Enabled | Experimental | Recommended For |
|-------|----------|---------|--------------|-----------------|
| `minimaxai/minimax-m3` | nvidia | ✅ true | ❌ false | ("literary", "balanced") |
| `gemini-2.5-flash` | gemini | ❌ false | ✅ true | ("planned",) |

The old Llama entry has been replaced with Minimax M3 as the default production model.

---

## 6. Provider Adapter Verified

- NVIDIA provider `default_model` → `minimaxai/minimax-m3` ✅
- NVIDIA provider `models[0].id` → `minimaxai/minimax-m3` ✅
- No hardcoded restriction preventing `minimaxai/minimax-m3` ✅
- Adapter correctly passes through `request.model` or falls back to `default_model` ✅

---

## 7. CLI Override Test

```powershell
python ntpe_launcher.py --validate-config
python ntpe_launcher.py --list-models
python ntpe_production_translate.py txt --help
python -m lts.txt_translation_runtime txt --help
```

All show `minimaxai/minimax-m3` as default. User can still pass `--model other-model` to override.

---

## 8. Old Model Reference Classification (Post-Migration)

| Category | Status |
|----------|--------|
| **CURRENT_PRODUCTION_DEFAULT** | **ELIMINATED** (0 remaining in 9 canonical locations) |
| **CURRENT_PRODUCTION_FALLBACK** | N/A (fallback models list is empty in provider_config.json) |
| **CURRENT_TEST_DEFAULT** | Present in test fixtures — **PRESERVED** (not production) |
| **HISTORICAL_EVIDENCE** | Present in artifacts/, manifests/, docs/releases/ — **PRESERVED** |
| **LEGACY** | Present in some legacy modules — **PRESERVED** |
| **DOCUMENTATION_HISTORY** | Present in release docs — **PRESERVED** |

**Key achievement:** Zero CURRENT_PRODUCTION_DEFAULT references to old model remain.

---

## 9. Validation Results

| Check | Result |
|-------|--------|
| `python ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing: `core.prompt_builder.prompt_builder` ModuleNotFoundError) |
| `git diff --check` | 3 CRLF warnings (pre-existing on literary outputs) |
| New failures | **NONE** |
| NEW_REGRESSIONS | **0** |

---

## 10. Safety Verification

| Metric | Value |
|--------|-------|
| Provider calls during validation | 0 |
| Network calls during validation | 0 |
| Real translation calls | 0 |
| Historical artifacts modified | 0 |
| Protected worktree modified | 0 (RM6 canary, monitoring tools preserved) |
| Root hygiene | COMPLIANT |

---

## 11. Git Safety

| Metric | Value |
|--------|-------|
| Staged | 0 |
| Committed (this phase) | 0 |
| Pushed (this phase) | 0 |
| HEAD | `8c999b1` |
| origin/main | `8c999b1` |
| Divergence | 0/0 |

---

## 12. STOP Conditions — All NOT Triggered

| Condition | Triggered? |
|-----------|------------|
| Production default in >9 locations | ❌ NO |
| Model precedence changed | ❌ NO |
| CLI override broken | ❌ NO |
| ENV override broken | ❌ NO |
| Adapter falls back to old model | ❌ NO |
| Unknown model restriction | ❌ NO |
| Historical artifacts modified | ❌ NO |
| Protected worktree modified | ❌ NO |
| UNKNOWN reference found | ❌ NO |
| New regression | ❌ NO |
| New validation error | ❌ NO |
| Provider call required | ❌ NO |
| Non-migration changes required | ❌ NO |
| Root hygiene violation | ❌ NO |

---

## 13. Deliverables

1. **Governance doc:** `docs/governance/repository/P0_FINAL_15_B_PRODUCTION_MODEL_MIGRATION.md`
2. **JSON report:** `artifacts/P0_FINAL_15_B_Production_Model_Migration_Report.json`

---

## 14. Final Verdict

**P0-FINAL-15-B = PASS**

- All 9 canonical production defaults updated to `minimaxai/minimax-m3` ✅
- Configuration precedence preserved ✅
- CLI/ENV override capability preserved ✅
- Model catalog synchronized ✅
- Provider adapter accepts new model ✅
- All launchers resolve to same new default ✅
- Zero CURRENT_PRODUCTION_DEFAULT references to old model ✅
- Historical evidence preserved ✅
- Validation passes ✅
- No new regressions ✅
- Working tree preserved ✅
- Zero STOP conditions triggered ✅

---

## 15. Next Phase: P0-FINAL-15-C

**Model Migration Validation / Reference Closure**

- Re-scan full repository for `meta/llama-3.3-70b-instruct`
- Classify all remaining references
- Confirm only historical/test/legacy references remain
- No production default references to old model exist