# Pre-Minimax Surgical Separation Plan

**Plan ID:** PRE_MINIMAX_SURGICAL_SEPARATION
**Timestamp:** 2026-08-29T17:01:12Z
**Repository:** D:\Python\NTPE
**Target Baseline:** 8c999b1
**Current HEAD:** 8c999b1 (main)
**Phase:** Phase 1 - Planning Only

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Verdict** | **SURGICAL_RECOVERY_READY** |
| Baseline Confirmed | ✅ 8c999b1 is HEAD, no subsequent commits |
| Total Changed Paths | 286 |
| Model-Only Files | 23 |
| Mixed Model/Runtime Files | 5 |
| Runtime-Only Files | 1 |
| New Feature | 1 (EPUB translation) |
| Runtime Improvements to Preserve | 7 |
| Recommended Strategy | **Strategy B** - Surgical hunk reversion |

---

## 1. Path-Level Classification

### 1.1 MODEL_ONLY (23 files)
*Pure model reference changes - revert completely*

```
config/default_config.json
config/launcher_product_defaults.json
config/models.json
core/adapters/production_submission_adapter.py
core/adaptive_context_authorized_provider_cli/config.py
core/adaptive_context_authorized_provider_cli/parser.py
core/adaptive_context_authorized_provider_harness/config.py
core/adaptive_context_controlled_provider_retry/config.py
core/adaptive_context_provider_execution_freeze/freeze.py
core/adaptive_context_real_provider_boundary/config.py
core/adaptive_context_real_provider_preflight/config.py
core/adaptive_context_real_provider_preflight/validator.py
core/adaptive_context_single_real_invocation/config.py
core/ai_provider/adapters.py
core/config.py
core/controlled_multi_chunk_translation_canary/policy.py
core/controlled_provider_routing/provider_profiles.py
core/controlled_provider_routing/routing_policy.py
core/controlled_translation_runtime_integration/policy.py
core/expansion/style_expansion_engine.py
core/launcher_product/config.py
core/launcher_product/model_catalog.py
core/lcr_production_shadow_hook/batch107_real_provider_validation.py
core/translation_quality_provider_canary/framework.py
```

### 1.2 NON_MODEL_ONLY (1 file)
*Pure runtime improvement - preserve completely*

```
core/translation_runtime/runtime_speed_policy.py
```

### 1.3 MIXED_MODEL_RUNTIME (5 files)
*Require hunk-level surgical separation*

| File | Model Hunks | Runtime Hunks | Action |
|------|-------------|---------------|--------|
| `core/translation_engine/provider_runtime.py` | 0 | 3 (RI-01, RI-02, RI-03) | RECONSTRUCT |
| `core/translation_engine/translation_engine.py` | 0 | 1 (RI-04) | RECONSTRUCT |
| `lts/txt_translation_runtime.py` | 1 (DEFAULT_MODEL) | 2 (RI-06, RI-07) | RECONSTRUCT |
| `config/provider_config.json` | 1 (default_model) | 2 (RI-05 globals) | RECONSTRUCT |
| `ntpe_production_translate.py` | 1 (DEFAULT_MODEL) | 2 (EPUB feature) | RECONSTRUCT |

### 1.4 TEST_MODEL_COUPLED (9 files)
*Test expectations tied to Minimax - revert expectations, regenerate outputs*

```
tests/unit/adapters/test_production_submission_adapter.py
tests/unit/test_controlled_provider_routing.py
tests/literary/outputs/PS-03-integration/Literary_Diff_Report.md
tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
tests/literary/outputs/PS-03-integration/Literary_Quality_Report.md
tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
tests/literary/outputs/Regression_History.json
tests/literary/outputs/Regression_History.md
```

### 1.5 REPOSITORY_CLEANUP (200+ files)
*Historical artifacts, obsolete tools, superseded docs - do NOT restore*

### 1.6 NEW_FEATURE (1 file)
*EPUB translation pipeline - preserve with model reverted*

```
ntpe_production_translate.py (epub subcommand)
```

---

## 2. Mixed-File Hunk Map

### 2.1 core/translation_engine/provider_runtime.py

| Hunk | Location | Classification | Reason |
|------|----------|----------------|--------|
| 1 | Lines 42-49: `NON_RETRYABLE_PROVIDER_ERROR_PATTERNS` | **KEEP_CURRENT** | Added "408" - HTTP 408 non-retryable classification (post-N1.5 decision) |
| 2 | Lines 187-196: `build_translation_provider_manager` signature | **KEEP_CURRENT** | Added `max_attempts`, `retry_base_delay_seconds` params for dynamic retry |
| 3 | Lines 220-231: `RetryPolicy` construction | **KEEP_CURRENT** | Uses dynamic params with config fallback |

**No model references in this file** - all 3 hunks are pure runtime improvements.

---

### 2.2 core/translation_engine/translation_engine.py

| Hunk | Location | Classification | Reason |
|------|----------|----------------|--------|
| 1 | Lines 213-221: `TranslationEngine.__call__` | **KEEP_CURRENT** | Passes `provider_attempts`/`retry_base_seconds` from metadata to provider |

**No model references in this file** - pure runtime propagation improvement.

---

### 2.3 lts/txt_translation_runtime.py

| Hunk | Location | Classification | Reason |
|------|----------|----------------|--------|
| 1 | Line 83: `DEFAULT_MODEL` constant | **REVERT_TO_8C999B1** | Model reference: `meta/llama-3.3-70b-instruct` → `minimaxai/minimax-m3` |
| 2 | Lines 889-898: Chunk metadata dict | **KEEP_CURRENT** | Adds `provider_attempts`, `retry_base_seconds` to metadata for propagation |
| 3 | Lines 1075-1122: Result handling | **KEEP_CURRENT** | New `incomplete` status + enhanced summary (successful_chunks/failed_chunks) |

---

### 2.4 config/provider_config.json

| Hunk | Location | Classification | Reason |
|------|----------|----------------|--------|
| 1 | Lines 2-6: Global `retry_defaults` | **KEEP_CURRENT** | `base_delay_seconds`: 0.0 → 5.0 (global resilience) |
| 2 | Lines 14-22: NVIDIA `retry_defaults` | **KEEP_CURRENT** | `max_attempts`: 1→3, `base_delay_seconds`: 0.0→5.0 (NVIDIA resilience) |
| 3 | Lines 34-38: NVIDIA `default_model` | **REVERT_TO_8C999B1** | Model reference: `meta/llama-3.3-70b-instruct` → `minimaxai/minimax-m3` |

---

### 2.5 ntpe_production_translate.py

| Hunk | Location | Classification | Reason |
|------|----------|----------------|--------|
| 1 | Lines 26-32: Imports | **KEEP_CURRENT** | EPUB adapter imports - model-agnostic |
| 2 | Line 99: `DEFAULT_MODEL` constant | **REVERT_TO_8C999B1** | Model reference only; EPUB uses this as CLI default fallback |
| 3 | Lines 193-628: `epub` subcommand + `run_epub()` | **KEEP_CURRENT** | Complete EPUB pipeline (~140 lines). Uses `--model` CLI arg (overridable). No Minimax-specific code. |

---

## 3. Seven Runtime Improvements Preservation Map

| ID | Name | File | Symbol/Hunk | Independent of Minimax |
|----|------|------|-------------|------------------------|
| **RI-01** | HTTP 408 Non-Retryable Classification | `provider_runtime.py` | `NON_RETRYABLE_PROVIDER_ERROR_PATTERNS` + "408" (Hunk 1) | ✅ Yes |
| **RI-02** | Dynamic Retry Config Parameters | `provider_runtime.py` | `build_translation_provider_manager(max_attempts, retry_base_delay_seconds)` (Hunk 2) | ✅ Yes |
| **RI-03** | Dynamic Retry Param Usage | `provider_runtime.py` | `RetryPolicy` construction with fallback (Hunk 3) | ✅ Yes |
| **RI-04** | Retry Config Propagation from Metadata | `translation_engine.py` | `TranslationEngine.__call__` passes metadata (Hunk 1) | ✅ Yes |
| **RI-05** | Balanced Profile Attempts Increase | `runtime_speed_policy.py` | `_POLICIES["balanced"].provider_attempts: 2→3` | ✅ Yes |
| **RI-06** | Partial Translation Handling | `txt_translation_runtime.py` | `incomplete` status on partial failure (Hunk 3) | ✅ Yes |
| **RI-07** | Retry Metadata + Enhanced Summary | `txt_translation_runtime.py` | Chunk metadata + summary fields (Hunk 2) | ✅ Yes |

**All 7 are confirmed independent of Minimax.** They form a coherent retry resilience stack:
- Config defaults (RI-05) → Dynamic override (RI-02/RI-03) → Metadata propagation (RI-07→RI-04) → Partial success handling (RI-06)
- 408 classification (RI-01) prevents inappropriate retries on provider timeouts

---

## 4. EPUB Feature Preservation Assessment

| Criterion | Assessment |
|-----------|------------|
| **Model-agnostic?** | ✅ Yes - Uses `--model` CLI argument, fully overridable |
| **Minimax-specific model ID?** | ❌ No - Only uses `DEFAULT_MODEL` as default fallback |
| **Minimax-specific provider changes?** | ❌ No - Uses existing `EpubExtractionBoundary`, `CanonicalBookIntakeAdapter`, `TxtTranslationOptions`, `TranslationRuntime` |
| **Preservable under pre-Minimax config?** | ✅ Yes - Just revert `DEFAULT_MODEL` constant |
| **Reconstruction needed?** | ❌ No - Complete feature, no partial dependencies |
| **Risk if lost** | **CRITICAL** - Entire production EPUB translation capability |

**Verdict: PRESERVE** — Revert only the `DEFAULT_MODEL` constant (Hunk 2), keep entire EPUB subcommand (Hunks 1, 3).

---

## 5. Deleted Paths Assessment

| Category | Count | Should Restore? | Risk |
|----------|-------|-----------------|------|
| Intentional cleanup (TE v6-v72 artifacts, book stages, NTPE v20, TIC batch3) | ~200 | ❌ No | LOW - Historical test evidence |
| Obsolete dev tools (`tools/one_shots/`) | 24 | ❌ No | LOW - Debugging utilities |
| Superseded governance doc | 1 | ❌ No | LOW - Documentation |
| **RM6 canary progress files** | **2** | **✅ Yes** | **MEDIUM** - Active canary state (shown as MODIFIED in git status) |

**Action:** Do not restore deleted artifacts/tools. Preserve the 2 modified RM6 canary files.

---

## 6. Test Separation Map

| Test File | Classification | Post-Recovery Action |
|-----------|----------------|---------------------|
| `test_production_submission_adapter.py` | Minimax-specific expectation | Revert assertion to `meta/llama-3.3-70b-instruct` |
| `test_controlled_provider_routing.py` | Minimax-specific expectation | Revert provider IDs to `nvidia-meta-llama-3.3-70b-instruct` |
| Literary outputs (7 files) | Minimax stage names/timestamps | **Regenerate** by running full literary regression suite |

**No separate generic resilience tests exist** — the literary regression suite covers runtime behavior. Must re-run post-recovery to establish new baselines with pre-Minimax model + preserved runtime improvements.

---

## 7. Recovery Strategy Comparison

### Strategy A: Reset → Reapply Patches
```
git reset --hard 8c999b1
→ apply 7 runtime patches + EPUB patch
```
| Factor | Assessment |
|--------|------------|
| Data Loss Risk | **HIGH** - 100 untracked P0-FINAL-15 report files orphaned |
| Regression Risk | MEDIUM - Patch conflicts, missing context |
| Traceability | LOW - Patches lose commit history |
| Testability | MEDIUM - All-or-nothing |
| Preserves EPUB/Runtime | Conditional on patch completeness |
| Effort | High (8+ patches to create/validate) |

### Strategy B: Surgical Hunk Reversion ⭐ **RECOMMENDED**
```
git checkout 8c999b1 -- <each MODEL_ONLY file>
→ manually edit 5 MIXED files per hunk map
```
| Factor | Assessment |
|--------|------------|
| Data Loss Risk | **NONE** - Working tree fully preserved |
| Regression Risk | **LOW** - Only targeted hunks reverted |
| Traceability | **HIGH** - Each change visible in git diff |
| Testability | **HIGH** - Incremental validation |
| Preserves EPUB/Runtime | **YES** - By construction |
| Effort | Medium (23 file resets + 5 surgical edits) |

**Rationale for Strategy B:** Zero data loss (preserves all P0-FINAL-15 artifacts), lower regression risk, better traceability, preserves improvements by construction. The 5 MIXED files have cleanly separable hunks with no interdependencies.

---

## 8. Proposed Recovery Allowlist (Files to Modify)

```
core/translation_engine/provider_runtime.py
core/translation_engine/translation_engine.py
core/translation_runtime/runtime_speed_policy.py
lts/txt_translation_runtime.py
config/provider_config.json
ntpe_production_translate.py
core/adapters/epub_extraction_boundary.py
core/adapters/canonical_book_intake_adapter.py
tests/unit/adapters/test_production_submission_adapter.py
tests/unit/test_controlled_provider_routing.py
```

## 9. Proposed Recovery Denylist (Files to Reset Completely)

All 23 MODEL_ONLY files listed in Section 1.1.

---

## 10. Validation Plan After Recovery

### Phase 1: Unit Tests
```bash
pytest tests/unit/adapters/test_production_submission_adapter.py -v
pytest tests/unit/test_controlled_provider_routing.py -v
pytest tests/unit/ -k 'provider' -v
```

### Phase 2: Runtime Behavior Verification
- [ ] `provider_runtime.py`: "408" in `NON_RETRYABLE_PROVIDER_ERROR_PATTERNS`
- [ ] `provider_runtime.py`: `build_translation_provider_manager` accepts dynamic params
- [ ] `translation_engine.py`: Passes `provider_attempts`/`retry_base_seconds` from metadata
- [ ] `runtime_speed_policy.py`: Balanced profile has `provider_attempts=3`
- [ ] `txt_translation_runtime.py`: Returns `incomplete` status on partial failure
- [ ] `txt_translation_runtime.py`: Metadata includes retry config

### Phase 3: Config Validation
- [ ] `provider_config.json`: Global retry `max_attempts=3`, `base_delay_seconds=5.0`
- [ ] `provider_config.json`: NVIDIA retry `max_attempts=3`, `base_delay_seconds=5.0`
- [ ] `provider_config.json`: NVIDIA `default_model = "meta/llama-3.3-70b-instruct"`
- [ ] `models.json`: NVIDIA default = `meta/llama-3.3-70b-instruct`
- [ ] `default_config.json`: `model = "meta/llama-3.3-70b-instruct"`

### Phase 4: EPUB Feature
- [ ] `ntpe_production_translate.py`: `epub` subcommand exists
- [ ] `ntpe_production_translate.py`: `DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"`
- [ ] CLI test: `python ntpe_production_translate.py epub --help`
- [ ] Dry-run test: `python ntpe_production_translate.py epub test.epub output/ --dry-run`

### Phase 5: Literary Regression
- [ ] Run full literary regression suite
- [ ] Verify `Regression_History.json` regenerates with pre-Minimax model
- [ ] Confirm retry resilience improvements function with old model

---

## 11. Final Verdict

### SURGICAL_RECOVERY_READY

**Selected Strategy:** Strategy B — Preserve Working Tree → Surgically Revert Model-Specific Hunks

**Files to Revert Completely (23):** All MODEL_ONLY files (Section 1.1)

**Files to Preserve Completely (3):**
- `core/translation_runtime/runtime_speed_policy.py`
- `artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json`
- `artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json`

**Mixed Files Requiring Hunk Reconstruction (5):**
- `core/translation_engine/provider_runtime.py` — Keep all 3 hunks
- `core/translation_engine/translation_engine.py` — Keep hunk 1
- `lts/txt_translation_runtime.py` — Revert hunk 1, keep hunks 2,3
- `config/provider_config.json` — Revert hunk 3, keep hunks 1,2
- `ntpe_production_translate.py` — Revert hunk 2, keep hunks 1,3

**Preserved Runtime Improvements (7):**
1. RI-01: HTTP 408 Non-Retryable Classification
2. RI-02: Dynamic Retry Configuration Parameters
3. RI-03: Dynamic Retry Parameter Usage in Provider Manager
4. RI-04: Retry Config Propagation from Metadata
5. RI-05: Balanced Profile Provider Attempts Increase (2→3)
6. RI-06: Partial Translation Handling (incomplete status)
7. RI-07: Retry Metadata in Chunk Pipeline + Enhanced Summary

**EPUB Preservation:** PRESERVE — Model-agnostic feature, only `DEFAULT_MODEL` constant reverted

**Deleted Path Risk:** LOW — 218 paths are intentional cleanup; 2 RM6 canary files are modified (not deleted) and will be preserved

**Test Summary:** 2 unit tests revert expectations; 7 literary outputs regenerate via regression suite

---

## 12. Next Step Recommendation

> **DO NOT EXECUTE RECOVERY IN THIS PHASE.**

**Required Implementation Phase (Phase 2):**
1. Execute Strategy B with explicit path allowlist (10 files in Section 8)
2. For each MODEL_ONLY file: `git checkout 8c999b1 -- <file>`
3. For each MIXED file: Manual edit per hunk map (Section 2)
4. Run validation plan (Section 10) incrementally
5. Re-run literary regression to establish new baselines
6. Commit surgical changes as atomic "Pre-Minimax Baseline + Runtime Improvements" commit

**Safety:** All operations in Phase 1 were read-only. No modifications made. Working tree intact.