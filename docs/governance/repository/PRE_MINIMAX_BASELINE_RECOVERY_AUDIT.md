# Pre-Minimax Baseline Recovery Audit

**Audit ID:** PRE_MINIMAX_BASELINE_RECOVERY_AUDIT
**Timestamp:** 2026-08-29T16:49:39Z
**Repository:** D:\Python\NTPE
**Target Baseline:** 8c999b1
**Current HEAD:** 8c999b1 (main branch)
**Auditor:** Kilo (read-only investigation)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Verdict** | **RECOVERY_TARGET_REQUIRES_REVIEW** |
| Target Baseline Confirmed | ✅ Yes (8c999b1 is HEAD, no subsequent commits) |
| Working Tree Clean | ❌ No (286 files changed, 100 untracked) |
| Model Migration Changes | 28 files (config + core + tests) |
| Non-Model Improvements | 7 critical changes in 4 co-modified files |
| New Features | 1 (EPUB translation pipeline) |
| Recovery Risk Level | **CRITICAL** (improvements intertwined with model changes) |

---

## 1. Git State Verification

### 1.1 Current Repository State
```
Branch: main
HEAD: 8c999b1 (P0-FINAL-13: clean governance repository surface)
Remote: origin/main (up to date)
```

### 1.2 Recent Commit History (Last 20)
```
8c999b1 (HEAD -> main, origin/main, origin/HEAD) P0-FINAL-13: clean governance repository surface
76ea24f P0-FINAL-12-R1: complete global migration reference closure
53e0476 P0-FINAL-12-B5 migrate tests away from historical artifacts
2bedad8 P0-FINAL-12-B4 CLI entrypoint reference migration
4de1c4a P0-FINAL-12-B3 runtime consumer reference migration
2ad6ac3 P0-FINAL-12-B2: migrate adapter and loader references
7136b42 P0-FINAL-12-B1: migrate canonical source references
5e346d1 DUMMY-TXT root filesystem side-effect remediation and closure
93d7498 P0 Repository Cleanup: Remove Test Artifacts (Batch F5-2)
... (11 more cleanup commits)
```

### 1.3 Baseline Commit Details (8c999b1)
- **Message:** P0-FINAL-13: clean governance repository surface
- **Files Changed:** 60 files (all governance/docs/archive artifacts)
- **Insertions:** 18,139 lines
- **Nature:** Governance documentation and archive manifest consolidation only
- **No production code changes**

### 1.4 Working Tree Status
| Category | Count |
|----------|-------|
| Deleted (staged/unstaged) | 218 |
| Modified | 31 |
| Untracked | 100 |
| **Total Changed** | **286** |

### 1.5 Diff Statistics (vs 8c999b1)
| Metric | Value |
|--------|-------|
| Files Changed | 286 |
| Insertions | 344 |
| Deletions | 114,003 |
| **Net Change** | **-113,659 lines** |

---

## 2. Changed Path Classification

### 2.1 MODEL / PROVIDER MIGRATION (28 files)
**Primary category — all model reference changes from `meta/llama-3.3-70b-instruct` to `minimaxai/minimax-m3`**

**Config (4):**
- `config/default_config.json`
- `config/launcher_product_defaults.json`
- `config/models.json`
- `config/provider_config.json` *(also contains retry config changes)*

**Core Production (22):**
- `core/adapters/production_submission_adapter.py`
- `core/adaptive_context_authorized_provider_cli/config.py`
- `core/adaptive_context_authorized_provider_cli/parser.py`
- `core/adaptive_context_authorized_provider_harness/config.py`
- `core/adaptive_context_controlled_provider_retry/config.py`
- `core/adaptive_context_provider_execution_freeze/freeze.py`
- `core/adaptive_context_real_provider_boundary/config.py`
- `core/adaptive_context_real_provider_preflight/config.py`
- `core/adaptive_context_real_provider_preflight/validator.py`
- `core/adaptive_context_single_real_invocation/config.py`
- `core/ai_provider/adapters.py`
- `core/config.py`
- `core/controlled_multi_chunk_translation_canary/policy.py`
- `core/controlled_provider_routing/provider_profiles.py`
- `core/controlled_provider_routing/routing_policy.py`
- `core/controlled_translation_runtime_integration/policy.py`
- `core/expansion/style_expansion_engine.py`
- `core/launcher_product/config.py`
- `core/launcher_product/model_catalog.py`
- `core/lcr_production_shadow_hook/batch107_real_provider_validation.py`
- `core/translation_quality_provider_canary/framework.py`

**Entry Points (2):**
- `lts/txt_translation_runtime.py`
- `ntpe_production_translate.py`

**Tests (2):**
- `tests/unit/adapters/test_production_submission_adapter.py`
- `tests/unit/test_controlled_provider_routing.py`

---

### 2.2 RUNTIME MODIFICATION (4 files)
**Critical non-model behavior changes co-located with model changes**

| File | Change | Impact |
|------|--------|--------|
| `core/translation_engine/provider_runtime.py` | Added `"408"` to `NON_RETRYABLE_PROVIDER_ERROR_PATTERNS` | HTTP 408 now non-retryable at provider level |
| `core/translation_engine/provider_runtime.py` | Added `max_attempts`, `retry_base_delay_seconds` params to `build_translation_provider_manager()` | Dynamic retry configuration |
| `core/translation_engine/translation_engine.py` | Passes `provider_attempts`, `retry_base_seconds` from metadata | Runtime retry config propagation |
| `core/translation_runtime/runtime_speed_policy.py` | `balanced` profile: `provider_attempts` 2 → 3 | Increased retry resilience |
| `lts/txt_translation_runtime.py` | Added `incomplete` status for partial success; retry metadata in chunks | Graceful partial translation handling |
| `config/provider_config.json` | NVIDIA retry: `base_delay_seconds` 0.0→5.0, `max_attempts` 1→3 | Major retry behavior improvement |

---

### 2.3 REPOSITORY / STRUCTURE MODIFICATION (218 deleted + 1 new feature)

**Deleted Artifacts (200+ files):**
- TE v6, v7, v71, v72 stage validation artifacts
- Book intake/preparation stage evidence
- Controlled multi-chunk translation stages
- NTPE v20 consolidation artifacts
- TIC batch3 alignment data (23k + 76k line JSON files)
- All RM6 canary progress files (2 modified, not deleted)

**Deleted Tools (24 files):**
- `tools/one_shots/launcher_*.py` (13 files)
- `tools/one_shots/write_*.py` (11 files)

**Deleted Governance Doc (1):**
- `docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_BATCH_D_RECONCILIATION.md`

**NEW FEATURE (not a deletion):**
- `ntpe_production_translate.py` — **Added `epub` subcommand** with full EPUB→TXT translation pipeline

---

### 2.4 TEST MODIFICATION (9 files)
- Literary test outputs updated with Minimax stage names and timestamps
- Unit test expectations updated for `minimaxai/minimax-m3`

---

### 2.5 GOVERNANCE MODIFICATION (1 file)
- Deleted governance reconciliation document

---

### 2.6 Other Categories
| Category | Count |
|----------|-------|
| PROMPT_MODIFICATION | 0 |
| TRANSLATION_QUALITY_MODIFICATION | 0 |
| UNKNOWN_REQUIRES_REVIEW | 0 |

---

## 3. Potentially Important Non-Model Changes

| # | File | Type | Description | Recovery Risk |
|---|------|------|-------------|---------------|
| 1 | `core/translation_engine/provider_runtime.py` | Runtime | HTTP 408 → non-retryable classification | **HIGH** — Provider error handling behavior change |
| 2 | `core/translation_engine/provider_runtime.py` | Runtime | Dynamic retry params (`max_attempts`, `retry_base_delay_seconds`) | **HIGH** — Loss of runtime retry configurability |
| 3 | `core/translation_engine/translation_engine.py` | Runtime | Metadata → provider retry config propagation | **HIGH** — Breaks retry config chain |
| 4 | `core/translation_runtime/runtime_speed_policy.py` | Runtime | Balanced profile attempts: 2 → 3 | **HIGH** — Reduced resilience |
| 5 | `lts/txt_translation_runtime.py` | Runtime | `incomplete` status + retry metadata | **MEDIUM** — Partial translation handling lost |
| 6 | `config/provider_config.json` | Runtime | NVIDIA retry: delay 0→5s, attempts 1→3 | **HIGH** — Major retry regression |
| 7 | `ntpe_production_translate.py` | **New Feature** | **EPUB translation pipeline** (extraction→intake→TXT pipeline) | **CRITICAL** — Entire production feature lost |

---

## 4. Suspected Minimax-Related Changes
All 28 MODEL/PROVIDER MIGRATION files + test expectation updates. Pattern: systematic replacement of:
- `meta/llama-3.3-70b-instruct` → `minimaxai/minimax-m3`
- Provider IDs: `nvidia-meta-llama-3.3-70b-instruct` → `nvidia-minimax-m3`
- ALLOWED_MODELS frozensets updated
- Model catalog display names updated

---

## 5. Recovery Risks Assessment

### 5.1 CRITICAL: Intertwined Changes
**Model changes and runtime improvements are co-located in the same files:**
- `core/translation_engine/provider_runtime.py` — Model ref + 408 classification + dynamic retry params
- `core/translation_engine/translation_engine.py` — Model ref + retry config propagation
- `lts/txt_translation_runtime.py` — Model ref + incomplete status + retry metadata
- `config/provider_config.json` — Model ref + retry defaults (0→5s, 1→3 attempts)

**A simple `git reset` would lose ALL runtime improvements.**

### 5.2 HIGH: EPUB Feature Loss
`ntpe_production_translate.py` gained a complete `epub` subcommand (~140 lines) with:
- EPUB extraction boundary integration
- Canonical book intake adapter
- Reuse of TXT translation pipeline
- Quality delivery hooks (RM-8.3)
- This is a **production feature**, not a model migration artifact.

### 5.3 HIGH: Retry Resilience Regression
Multiple files implement a coherent retry strategy:
- Provider config: 3 attempts, 5s base delay
- Speed policy: 3 attempts for balanced
- Provider runtime: dynamic override capability
- Translation engine: metadata propagation
- TXT runtime: chunk-level metadata

**Losing this would revert to: 1 attempt, 0 delay, no dynamic config.**

### 5.4 MEDIUM: Partial Translation Handling
New `incomplete` status in `txt_translation_runtime.py` allows returning partial results instead of total failure.

### 5.5 LOW: Artifact/Tool Cleanup
218 deleted artifact files and 24 one-shot tools are historical/debugging debris. Recovery would restore clutter but not affect production.

---

## 6. Co-Modification Analysis (Critical Finding)

The following files contain **BOTH** model migration changes **AND** non-model improvements:

| File | Model Changes | Non-Model Changes |
|------|---------------|-------------------|
| `core/translation_engine/provider_runtime.py` | Model default in comments/constants | 408 classification, dynamic retry params |
| `core/translation_engine/translation_engine.py` | Model default in metadata handling | Retry config propagation from metadata |
| `lts/txt_translation_runtime.py` | `DEFAULT_MODEL` constant | `incomplete` status, chunk retry metadata |
| `config/provider_config.json` | NVIDIA default_model | Retry defaults (attempts, delay) |
| `ntpe_production_translate.py` | `DEFAULT_MODEL` constant | **Entire EPUB subcommand** |

**This co-location makes clean separation impossible via file-level operations.**

---

## 7. Final Verdict

### RECOVERY_TARGET_REQUIRES_REVIEW

**Rationale:**
1. ✅ **Baseline confirmed:** 8c999b1 is HEAD with no subsequent commits
2. ✅ **Model migration scope identified:** 28 files, systematic model reference replacement
3. ❌ **Clean recovery impossible:** 7 critical non-model improvements in 4 co-modified files
4. ❌ **New feature at risk:** EPUB translation pipeline would be lost
5. ❌ **Retry resilience regression:** Coherent retry strategy would be destroyed

---

## 8. Recommended Next Action

> **DO NOT EXECUTE RECOVERY IN THIS PHASE.**

### Required: Surgical Separation Phase
Before any baseline recovery, a separate implementation task must:

1. **Create patches** for all 7 non-model improvements from current working tree
2. **Verify patches apply cleanly** to 8c999b1 baseline
3. **Define explicit path allowlist** for the separation work
4. **Execute recovery** (reset to 8c999b1) **only after** patches are validated
5. **Apply patches** post-recovery to preserve improvements

### Alternative: Cherry-Pick Forward
- Create clean branch from 8c999b1
- Cherry-pick non-model improvement commits (if they exist as separate commits)
- Or manually apply the 7 improvements as new commits

### Path Allowlist for Separation Phase
```
core/translation_engine/provider_runtime.py
core/translation_engine/translation_engine.py
core/translation_runtime/runtime_speed_policy.py
lts/txt_translation_runtime.py
config/provider_config.json
ntpe_production_translate.py
core/adapters/epub_extraction_boundary.py
core/adapters/canonical_book_intake_adapter.py
```

---

## 9. Read-Only Checks Pass/Fail

| Check | Status |
|-------|--------|
| `git status` | ✅ PASS |
| `git branch --show-current` | ✅ PASS |
| `git log --oneline --decorate -n 20` | ✅ PASS |
| `git show --stat --oneline 8c999b1` | ✅ PASS |
| `git diff 8c999b1 --stat` | ✅ PASS |
| `git diff 8c999b1 --name-status` | ✅ PASS |
| No modifications made | ✅ PASS |
| No files deleted | ✅ PASS |
| No files overwritten | ✅ PASS |
| No git reset/checkout/push | ✅ PASS |

---

## 10. Artifacts Generated

1. `artifacts/PRE_MINIMAX_BASELINE_RECOVERY_AUDIT.json` — Machine-readable audit data
2. `docs/governance/repository/PRE_MINIMAX_BASELINE_RECOVERY_AUDIT.md` — This report

---

**End of Audit** — No recovery operations performed. All safety rules observed.