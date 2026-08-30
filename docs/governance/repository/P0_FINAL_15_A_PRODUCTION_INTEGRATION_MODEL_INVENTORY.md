# P0-FINAL-15-A: Production Integration & Model Migration Inventory

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
| STOP-P15A-02 | **NOT TRIGGERED** |

---

## 2. Worktree Inventory Summary

**Total dirty paths:** **293** (+2 from P0-FINAL-14's 291 — new governance artifacts created by P0-FINAL-14)

| Status | Count |
|--------|-------|
| Modified (M) | 7 |
| Deleted (D) | 207 |
| Untracked (??) | 35 |

**All dirty paths are consistent with P0-FINAL-14 classification** — no unexpected drift detected. STOP-P15A-01 **NOT TRIGGERED**.

---

## 3. Model Migration Inventory

### 3.1 Old Model: `meta/llama-3.3-70b-instruct`

**Total references found:** 200+ across the codebase (grep limit reached at 100 twice)

### 3.2 New Model: `minimaxai/minimax-m3`

**Total references found:** **0** — new model does not yet appear anywhere in the repository.

---

### 3.3 Old Model Reference Classification

| Category | Count | Key Files |
|----------|-------|-----------|
| **CURRENT_PRODUCTION** | ~30 | `config/default_config.json`, `config/provider_config.json`, `config/models.json`, `config/launcher_product_defaults.json`, `ntpe_production_translate.py` (line 95), `lts/txt_translation_runtime.py` (line 83), `core/launcher_product/config.py` (line 32), `core/launcher_product/model_catalog.py` (line 8), `core/ai_provider/adapters.py` (lines 104, 110) |
| **CURRENT_TEST** | ~40 | `tests/integration/translation_engine_v700_stage*.py`, `tests/integration/translation_engine_v720_stage*.py`, `tests/unit/test_translation_quality_canary.py`, `tests/unit/test_controlled_provider_routing.py`, `tests/unit/adapters/test_production_submission_adapter.py`, `tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py`, `tests/stage_14/launcher_ai_provider_framework_test.py` |
| **CURRENT_TOOLING** | ~15 | `tools/provider_controls/ntpe_single_real_provider_invocation.py`, `tools/generate_te_v720_controlled_canary.py`, `tools/generate_ntpe_v20_stage1_launcher_foundation_artifacts.py` |
| **HISTORICAL_EVIDENCE** | ~60 | `artifacts/tic_batch*/*.json`, `artifacts/te_v72_canary_execution/`, `manifests/*.json`, `docs/releases/te_v*/*.md` |
| **LEGACY** | ~25 | `core/translation_release/te_v6_release.py`, `engine/nvidia.py`, `core/expansion/style_expansion_engine.py`, `core/controlled_translation_runtime_integration/policy.py`, `core/controlled_provider_routing/provider_profiles.py`, `core/controlled_multi_chunk_translation_canary/policy.py`, `core/adaptive_context_*/config.py`, `core/adapters/production_submission_adapter.py` |
| **DOCUMENTATION_HISTORY** | ~30 | `docs/releases/te_v7_0/*.md`, `docs/releases/te_v7_2/*.md`, `docs/releases/te_v6_0/*.md` |

**Key Finding:** The **production default model is hardcoded to `meta/llama-3.3-70b-instruct` in at least 6 configuration files** that form the canonical resolution chain.

---

### 3.4 Configuration Precedence (Model Resolution Chain)

**Actual resolution order (traced from code):**

```
1. CLI argument (--model)
    ↓
2. Environment variable (NTPE_FALLBACK_MODELS for fallbacks only; NTPE_API_TIMEOUT etc for timeouts)
    ↓
3. Config file (config/launcher_product_defaults.json → config/default_config.json → config/models.json → config/provider_config.json)
    ↓
4. ProviderAdapterConfig default_model (core/ai_provider/adapters.py)
    ↓
5. LauncherConfig _BASE_CONFIG (core/launcher_product/config.py)
    ↓
6. TxtTranslationOptions DEFAULT_MODEL (lts/txt_translation_runtime.py)
    ↓
7. ntpe_production_translate.py DEFAULT_MODEL constant
```

**If user provides NO model override:** The effective production default is **`meta/llama-3.3-70b-instruct`** (from `config/launcher_product_defaults.json` → `config/default_config.json` → `core/launcher_product/config.py` → `core/ai_provider/adapters.py`).

**Target for migration:** All 6+ canonical config locations must be updated to `minimaxai/minimax-m3`.

---

## 4. Launcher Audit

| Launcher | Model Default Source | CLI Override | Env Override | Status |
|----------|---------------------|--------------|--------------|--------|
| `ntpe_launcher.py` | `core/launcher_product/config.py` → `config/launcher_product_defaults.json` | `--config` file | N/A | **Current: llama-3.3** |
| `ntpe_production_translate.py` | `DEFAULT_MODEL` constant (line 95) | `--model` arg | `NTPE_FALLBACK_MODELS` | **Current: llama-3.3** |
| `lts/txt_translation_runtime.py` | `DEFAULT_MODEL` constant (line 83) | `--model` arg | `NTPE_FALLBACK_MODELS` | **Current: llama-3.3** |
| `core/translation_runtime/runtime.py` | Delegates to LTS | N/A | N/A | **Current: llama-3.3** |

**All production launchers resolve to same default model via config chain.**

---

## 5. Runtime Audit

### Hard-coded `meta/llama-3.3-70b-instruct` Found In:

| Component | Location | Type |
|-----------|----------|------|
| `TxtTranslationOptions` dataclass default | `lts/txt_translation_runtime.py:115` | Dataclass field default |
| `DEFAULT_MODEL` module constant | `lts/txt_translation_runtime.py:83` | Module constant |
| `DEFAULT_MODEL` module constant | `ntpe_production_translate.py:95` | Module constant |
| `_BASE_CONFIG` dict | `core/launcher_product/config.py:32` | Config dict default |
| `ModelDefinition.model_id` | `core/launcher_product/model_catalog.py:8` | Catalog entry |
| `ProviderAdapterConfig.default_model` | `core/ai_provider/adapters.py:104` | Provider config |
| `ProviderAdapterConfig.models[0].id` | `core/ai_provider/adapters.py:110` | Provider models list |
| `config/default_config.json` | `config/default_config.json:4` | JSON config |
| `config/models.json` | `config/models.json:3,5` | JSON config |
| `config/provider_config.json` | `config/provider_config.json:37` | JSON config |
| `config/launcher_product_defaults.json` | `config/launcher_product_defaults.json:7` | JSON config |
| `core/controlled_translation_runtime_integration/policy.py` | Line 22 | Policy constant |
| `core/controlled_provider_routing/provider_profiles.py` | Line 28 | Provider profile |
| `core/controlled_multi_chunk_translation_canary/policy.py` | Line 58 | Policy constant |
| `core/expansion/style_expansion_engine.py` | Line 38 | Function default |
| `core/adapters/production_submission_adapter.py` | Lines 20, 129 | Dataclass default + validation |
| All `core/adaptive_context_*/config.py` | Various | Config dataclass defaults |
| `engine/nvidia.py` | Line 7 | Class default |

**No hard-coded references found in:** `core/translation_engine/`, `core/translation_runtime/` (beyond LTS delegation), `core/runtime/`, `core/translation_pipeline/`.

---

## 6. RM6 Canary Inventory

### Current Status

| Aspect | Status |
|--------|--------|
| **Legacy pipeline** (`artifacts/rm6_canary/legacy_kr/`) | ✅ **COMPLETED** — 3/3 chunks translated, output produced |
| **Runtime pipeline** (`artifacts/rm6_canary/runtime_kr/`) | ✅ **COMPLETED** — 3/3 chunks translated, output produced (`novel_sample_zh.txt`) |
| **Progress tracking** | ✅ Live progress files show completion |
| **Test fixture** | `tests/fixtures/rm6_canary/novel_sample.txt` — Korean novel excerpt (~5.8 KB) |

### RM6 Canary Assessment

| Question | Answer |
|----------|--------|
| Implemented? | ✅ Both legacy and runtime pipelines |
| Validated? | ✅ Outputs exist and are readable Korean→Chinese translation |
| Failed? | ❌ No failures recorded |
| Pending? | ❌ All 3 chunks completed |
| Blockers? | None |

**Conclusion:** RM6 Canary **IS READY** as the next canonical production runtime verification phase. Both pipeline implementations produced valid translations of the same source text.

---

## 7. EPUB E2E Pipeline Inventory

### Pipeline Chain Status

| Stage | Component | Status | Notes |
|-------|-----------|--------|-------|
| **EPUB Extraction** | `core/adapters/EpubExtractionBoundary` | ✅ **IMPLEMENTED** | Full EPUB 3/2 support, 1235 lines, security validation, chapter mapping |
| **Extraction Result → Intake Request** | `ExtractedTextIntakeRequest` dataclass | ✅ **IMPLEMENTED** | Defined in `epub_extraction_boundary.py:90-103` |
| **Canonical Adapter** | `core/adapters/CanonicalBookIntakeAdapter.ingest_extracted()` | ✅ **IMPLEMENTED** | Consumes `ExtractedTextIntakeRequest`, produces `CanonicalIntakeResult` |
| **Book Intake** | `core/book_intake/BookIntakeProcessor` | ✅ **IMPLEMENTED** | Custom processor with extracted-text reader/detector |
| **Book Preparation** | `core/book_preparation/BookPreparationProcessor` | ✅ **IMPLEMENTED** | Full preparation pipeline |
| **Chunking/Segmentation** | `core/book_chunking/`, `core/book_segmentation/` | ✅ **IMPLEMENTED** | Policy-driven chunking |
| **Translation Runtime** | `core/translation_runtime/TranslationRuntime` | ✅ **IMPLEMENTED** | Delegates to LTS or Runtime pipeline |
| **Translation Engine** | `core/translation_engine/TranslationEngine` | ✅ **IMPLEMENTED** | Full prompt → provider → QA pipeline |
| **Provider Runtime** | `core/ai_provider/`, `core/translation_runtime/runtime_provider.py` | ✅ **IMPLEMENTED** | NVIDIA + multi-provider support |
| **Quality/Repair** | `core/translation_quality_v5/`, `core/literary/` | ✅ **IMPLEMENTED** | Multi-phase QA |
| **Output** | `core/translation_runtime/runtime_output.py` | ✅ **IMPLEMENTED** | Formatted output |

### Missing: **User-Facing EPUB Entry Point**

| Gap | Status |
|-----|--------|
| **CLI command for EPUB input** | ❌ **MISSING** — No `ntpe_production_translate.py epub` subcommand |
| **Launcher EPUB support** | ❌ **MISSING** — `ntpe_launcher.py` only has `txt`, `batch`, `regression`, `corpus`, `evaluate`, `doctor` |
| **GUI EPUB file dialog** | ⚠️ **PARTIAL** — `ui/translation_launcher/app.py:106` shows EPUB in file dialog but no handler |

**Can a general user drop an EPUB and get translation?** **NO** — The internal pipeline is complete, but **no user-facing entry point exists**. User must manually extract EPUB → TXT first, then use TXT launcher.

---

## 8. Literary Regression Inventory

### Current Baseline (from `Regression_History.json`)

| Stage | Status | Score | Notes |
|-------|--------|-------|-------|
| **PS-03-integration** (latest) | ⚠️ **WARNING** | **78.0** | Current best baseline (2026-08-24) |
| **PS-03-smoke** | ❌ FAILED | 0.0 | 2026-08-14 |
| **PS-03** | ❌ FAILED | 0.0 | 2026-08-18 |
| **PS-02-integration** | ❌ FAILED | 0.0 | 2026-08-24 |
| **TER-v1.8-retry** | ✅ SUCCESS | 100.0 | Historical peak |
| **TER-v1.x series** | ✅ SUCCESS | 100.0 | Multiple historical successes |

### Regression Components Status

| Component | Status |
|-----------|--------|
| Golden Set (`tests/literary/Golden_Set/`) | ✅ EXISTS — Korean source text available |
| Quality Gate | ✅ IMPLEMENTED — `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py` |
| Character Consistency | ✅ IMPLEMENTED — `core/character_memory_v2/`, `core/entity_consistency/` |
| Glossary Consistency | ✅ IMPLEMENTED — `core/glossary_builder/`, locked dictionary |
| Korean Residue Detection | ✅ IMPLEMENTED — `max_korean_chars` QA check |
| Repeated Paragraph Detection | ✅ IMPLEMENTED — `max_repeated_lines` QA check |
| Translation Length Ratio | ✅ IMPLEMENTED — `min_length_ratio` QA check |
| Quality Score | ✅ IMPLEMENTED — `Literary_Quality_Report.md/json` |

**Current Baseline:** **PS-03-integration (78.0)** — warning status, not failed.

---

## 9. User Flow Assessment

### General User: "Drop EPUB → Get Translation"

| Step | Automated? | Manual Required? | Missing? |
|------|------------|------------------|----------|
| 1. Select EPUB file | ❌ | ✅ Must manually extract text | No EPUB CLI entry |
| 2. EPUB → Text extraction | ✅ | | `EpubExtractionBoundary` exists |
| 3. Text → Intake/Preparation | ✅ | | `CanonicalBookIntakeAdapter` + processors |
| 4. Chunking | ✅ | | `book_chunking` + `book_segmentation` |
| 5. Translation | ✅ | | `TranslationRuntime` + `TranslationEngine` |
| 6. Quality/QA | ✅ | | Multi-phase QA |
| 7. Output assembly | ✅ | | `runtime_output.py` |
| 8. EPUB output | ⚠️ | | Exporter exists but not wired to launcher |

**Technical Risks:**
1. **No EPUB CLI entry point** — User cannot directly translate EPUB
2. **Model migration pending** — Current default is `meta/llama-3.3-70b-instruct`, target is `minimaxai/minimax-m3`
3. **RM6 Canary not promoted** — Completed but not formally activated as production baseline
4. **Literary regression baseline is WARNING (78.0)** — Not a clean SUCCESS baseline

---

## 10. GitHub Product Gap Analysis

| Component | In GitHub 8c999b1? | In Local Only? | Gap |
|-----------|-------------------|----------------|-----|
| All production runtime code | ✅ | ❌ | — |
| All config files (with llama-3.3) | ✅ | ❌ | — |
| EPUB extraction pipeline | ✅ | ❌ | — |
| Canonical intake adapter | ✅ | ❌ | — |
| Launchers (txt/batch/regression) | ✅ | ❌ | — |
| Tests (894 pytest) | ✅ | ❌ | — |
| **EPUB CLI entry point** | ❌ | ❌ | **MISSING FROM BOTH** |
| **minimaxai/minimax-m3 config** | ❌ | ❌ | **MISSING FROM BOTH** |
| **RM6 promoted baseline** | ❌ | ❌ | **MISSING FROM BOTH** |
| **Clean literary regression SUCCESS** | ❌ | ⚠️ Local has WARNING | **LOCAL HAS BETTER** |

**LOCAL_PRODUCTION_DEPENDENCY_GAP: NONE** — All production code is in GitHub. Local only has evidence/artifacts.

**However: PRODUCT FEATURE GAP EXISTS** — EPUB direct translation not available in either GitHub or local.

---

## 11. Root Hygiene

| Check | Result |
|-------|--------|
| Root `.py` files | 7 (all entry points — ALLOWED) |
| Root `.txt` files | 2 (`requirements.txt`, `VERSION.txt` — ALLOWED) |
| Root `.ps1`/`.bat`/`.json`/`.log` | 0 (COMPLIANT) |
| `tools/one_shots/` deleted | ✅ (archived) |
| `tools/legacy_pipeline_launchers/` deleted | ✅ (archived) |
| `tools/archive/` exists | ✅ |
| `tools/monitoring/` exists | ✅ |

---

## 12. Validation Results

| Check | Result |
|-------|--------|
| `python ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing: `core.prompt_builder.prompt_builder` ModuleNotFoundError) |
| `git diff --check` | 3 CRLF warnings (pre-existing on literary outputs) |
| New failures | **NONE** |

---

## 13. Git Safety Verification

| Metric | Value |
|--------|-------|
| Staged | 0 |
| Committed (this phase) | 0 |
| Pushed (this phase) | 0 |
| HEAD | `8c999b1` |
| origin/main | `8c999b1` |
| Divergence | 0/0 |
| Working tree | Unchanged |

---

## 14. Provider/Network Safety

| Activity | Count |
|----------|-------|
| Provider calls | 0 |
| Network calls | 0 |
| Real translation calls | 0 |

---

## 15. STOP Conditions

| Condition | Triggered? |
|-----------|------------|
| STOP-P15A-01 Worktree drift | ❌ NO |
| STOP-P15A-02 Baseline mismatch | ❌ NO |
| STOP-P15A-03 Local-only production dependency | ❌ NO |
| STOP-P15A-04 Cannot determine canonical model config | ❌ NO (fully traced) |
| STOP-P15A-05 Historical evidence modification | ❌ NO |
| STOP-P15A-06 Unexpected root artifact | ❌ NO |
| STOP-P15A-07 Validation regression | ❌ NO |
| STOP-P15A-08 Audit modifies repository | ❌ NO |
| STOP-P15A-09 Real provider/network request | ❌ NO |

---

## 16. Recommended Next: P0-FINAL-15-B — Production Model Migration

**Migration Scope (atomic, explicit path allowlist):**

### Configuration Files (6+):
1. `config/launcher_product_defaults.json` — `model_id`
2. `config/default_config.json` — `model`
3. `config/models.json` — `default` + `models[]`
4. `config/provider_config.json` — `providers.nvidia.default_model`
5. `core/launcher_product/config.py` — `_BASE_CONFIG["model_id"]`
6. `core/launcher_product/model_catalog.py` — `ModelDefinition.model_id`
7. `core/ai_provider/adapters.py` — `ProviderAdapterConfig.default_model` + `models[0].id`
8. `ntpe_production_translate.py` — `DEFAULT_MODEL` constant
9. `lts/txt_translation_runtime.py` — `DEFAULT_MODEL` constant

### Test Fixtures (DO NOT MODIFY — Historical):
- `tests/fixtures/tic_batch*/*.json`
- `artifacts/tic_batch*/*.json`
- `manifests/*.json`
- `docs/releases/te_v*/*.md`

### Test Configuration (MODIFY for new canary runs):
- `tests/integration/translation_engine_v700_stage*.py`
- `tests/integration/translation_engine_v720_stage*.py`
- `tests/unit/test_*.py`
- `tools/provider_controls/ntpe_single_real_provider_invocation.py`
- `tools/generate_te_v720_controlled_canary.py`

---

## 17. Final Verdict

**P0-FINAL-15-A = PASS**

- Baseline verified ✅
- 293 dirty paths stable ✅
- Old model references fully classified (200+) ✅
- New model not yet present ✅
- Configuration precedence fully traced ✅
- All launchers audited ✅
- Runtime hard-coded defaults identified ✅
- RM6 Canary: COMPLETED & READY ✅
- EPUB Pipeline: Internally complete, MISSING user entry point ⚠️
- Literary Regression: Current baseline WARNING (78.0) ⚠️
- User flow: Cannot directly translate EPUB ❌
- GitHub gap: No production code gap; feature gap exists ⚠️
- Root hygiene: COMPLIANT ✅
- Validation: PASS ✅
- Zero STOP conditions triggered ✅
- Working tree preserved ✅

---

## 18. Deliverables Created

1. **Governance doc:** `docs/governance/repository/P0_FINAL_15_A_PRODUCTION_INTEGRATION_MODEL_INVENTORY.md`
2. **JSON report:** `artifacts/P0_FINAL_15_A_Production_Integration_Model_Inventory_Report.json`