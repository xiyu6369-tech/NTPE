# Phase 3D.1 — Production Execution Path & Legacy Route Closure Audit

**Status**: `P3D1_LEGACY_REACHABLE`
**Baseline**: `e0b60071777aa624b43ecf82d7c88c40da4a636c`
**Migration Commit**: `e0b6007`
**Active Model**: `meta/llama-3.2-90b-vision-instruct`
**Date**: 2026-08-30

---

## 1. Baseline Lock Verification

```powershell
git rev-parse HEAD
# e0b60071777aa624b43ecf82d7c88c40da4a636c

git status --short
# (clean - only untracked Phase 3D/3D.1 artifacts)

git diff --stat
# (no changes)
```

✅ **Baseline integrity verified**: HEAD = e0b6007, working tree clean

---

## 2. Canonical Production Path

**Single canonical path confirmed:**

```
User Entry: CLI (ntpe_production_translate.py subcommands: txt/batch/epub/regression)
    ↓
CLI Parser: ntpe_production_translate.py:build_parser()
    ↓
Runtime Facade: core/translation_runtime/runtime.py:TranslationRuntime
    ↓
TXT/Batch Runtime: lts/txt_translation_runtime.py:translate_txt() / lts/batch_translation_runtime.py:translate_batch()
    ↓
Runtime Pipeline: lts/txt_translation_runtime.py:_translate_txt_with_runtime_pipeline() (RuntimeOrchestrator)
    ↓
Translation Engine: core/translation_engine/translation_engine.py:TranslationEngine
    ↓
Provider Manager: core/translation_engine/provider_runtime.py:build_translation_provider_manager()
    ↓
NVIDIA Provider: core/translation_engine/provider_runtime.py:NvidiaTranslationProvider
    ↓
NVIDIA Client: core/translation_engine/nvidia_client.py:NvidiaClient
    ↓
NVIDIA API: https://integrate.api.nvidia.com/v1/chat/completions
    ↓
Model: meta/llama-3.2-90b-vision-instruct
```

---

## 3. Production Translation Entry Points

| Entry Point | File | Function | Classification | Pipeline Mode |
|-------------|------|----------|----------------|---------------|
| txt | ntpe_production_translate.py | run_txt | PRODUCTION_CANONICAL | runtime (default) / legacy (opt-in) |
| batch | ntpe_production_translate.py | run_batch | PRODUCTION_CANONICAL | runtime (default) / legacy (opt-in) |
| epub | ntpe_production_translate.py | run_epub | PRODUCTION_CANONICAL | runtime (default) / legacy (opt-in) |
| regression | ntpe_production_translate.py | run_regression | PRODUCTION_SECONDARY | runtime (default) |

**No other production-capable entry points found.**

---

## 4. Legacy Production Routes (CRITICAL FINDING)

### 4.1 LTS Legacy Pipeline Branch

**Status**: `ACTIVE_LEGACY_REACHABLE` (HIGH RISK)

- **Location**: `lts/txt_translation_runtime.py:1965-2145` (legacy branch in `translate_txt()`)
- **Activation**: `--pipeline=legacy` CLI flag or `NTPE_RUNTIME_PIPELINE=legacy` env var
- **Default**: `runtime` (legacy is opt-in)
- **Differences from canonical**:
  - Builds prompt packages inline via `build_prompt_package()` vs RuntimeOrchestrator
  - Uses `translate_package_with_retry()` directly vs RuntimeProviderAdapter
  - Has explicit QA retry loop with adaptive feedback vs quality gates
- **Convergence**: Both paths end at same `TranslationEngine → provider_runtime → NvidiaClient`

### 4.2 EPUB Legacy Pipeline Branch

**Status**: `ACTIVE_LEGACY_REACHABLE` (HIGH RISK)

- **Location**: `ntpe_production_translate.py:run_epub()` with `--pipeline=legacy`
- **Path**: EPUB extraction → temp TXT → `run_txt()` with legacy mode
- **Activation**: Same `--pipeline=legacy` flag

### 4.3 Batch Legacy Pipeline Branch

**Status**: `ACTIVE_LEGACY_REACHABLE` (HIGH RISK)

- **Location**: `ntpe_production_translate.py:run_batch()` with `--pipeline=legacy`
- **Path**: Batch → `translate_batch()` → `translate_txt()` with legacy mode
- **Activation**: Same `--pipeline=legacy` flag

---

## 5. Model Route Audit

✅ **Active Production Model**: `meta/llama-3.2-90b-vision-instruct` (56 locations migrated in Phase 3D)

✅ **Rejected/EOL Models Production Reachable**: **NONE**

| Model | Classification | Production Reachable |
|-------|----------------|---------------------|
| meta/llama-3.3-70b-instruct | HISTORICAL_ONLY | NO |
| minimaxai/minimax-m3 | HISTORICAL_ONLY | NO |
| nvidia/llama-3.1-nemotron-70b-instruct | HISTORICAL_ONLY | NO |
| nvidia/riva-translate-4b-instruct-v2 | HISTORICAL_ONLY | NO |
| DeepSeek-V4 | HISTORICAL_ONLY | NO |

All historical references confined to:
- `archive/` directory (excluded from production imports)
- P3A/P3B artifacts (evidence preservation)
- Stage 10.x frozen validation tests (MODEL constants for historical validation)
- Diagnostic tools in `tools/one_shots/`

✅ **Fallback Models**: Configurable via `NTPE_FALLBACK_MODELS` / `--fallback-models` but **NONE active by default**

---

## 6. Duplicate Runtime / Provider / Retry / Timeout Audit

| Check | Result |
|-------|--------|
| Duplicate Translation Runtime | NO - single canonical runtime; legacy branch is explicit opt-in |
| Duplicate Provider Runtime | NO - single NVIDIA provider path |
| Duplicate Retry | NO - proper separation: LTS (outer, model fallback) → ProviderManager (inner, transient errors) → RuntimeAdapter (disabled) |
| Nested Retry | NO - each layer handles distinct error classes |
| Conflicting Timeout | NO - proper priority: CLI > env explicit > speed policy > defaults |
| Legacy Prompt Path | NO - both paths use `LiteraryPromptBuilder` |
| Legacy Context Path | NO - canonical path; adaptive modules feature-gated |

---

## 7. Retry Chain Analysis

```
LTS Retry (outer) → translate_package_with_retry()
    Handles: model fallback chain (NTPE_FALLBACK_MODELS), provider_attempts
    Max attempts: configurable (default 4)

    ↓ calls

RuntimeProviderAdapter Retry (disabled by default)
    Max retries: 0
    Policy: RuntimeProviderPolicy(max_retries=0)

    ↓ calls

ProviderManager Retry (inner)
    Handles: transient provider errors (503, 429, timeout, etc.)
    Max attempts: 3 (from provider_config.json)
    Base delay: 10s, backoff: 2x
```

**No duplicate or nested retry for same error class.**

---

## 8. Timeout Priority Chain

```
1. Explicit CLI --api-timeout / --api-connect-timeout
2. NTPE_API_TIMEOUT_EXPLICIT=1 (makes env vars authoritative)
3. NTPE_API_TIMEOUT / NTPE_API_CONNECT_TIMEOUT env vars
4. Speed policy (_effective_provider_timeout: 90s first attempt for short chunks)
5. NTPE_SHORT_CHUNK_FIRST_TIMEOUT env (90s default)
6. Defaults (60s / 10s)
```

**Proper cascading confirmed.**

---

## 9. EPUB / TXT Path Convergence

| Aspect | TXT | EPUB |
|--------|-----|------|
| Intake | Direct file read | `EpubExtractionBoundary` → `CanonicalBookIntakeAdapter` |
| Normalization | `split_text()` | Extracted text → temp TXT file |
| Translation | `translate_txt()` | Delegates to `translate_txt()` |
| Pipeline Mode | `--pipeline` flag respected | Same `--pipeline` flag respected |
| **Convergence** | **Canonical runtime (default)** | **Canonical runtime (default)** |

✅ **Both converge on same canonical runtime when --pipeline=runtime (default)**

---

## 10. Adaptive/Controlled Runtime Reachability

| Module | Classification | Production Reachable |
|--------|---------------|---------------------|
| core/adaptive_context_runtime_shadow | TEST_ONLY/HISTORICAL | NO (no-op-unless-shadow) |
| core/adaptive_context_canary_* | TEST_ONLY | NO |
| core/adaptive_context_production_* | TEST_ONLY/HISTORICAL | NO |
| core/adaptive_context_activation_policy | FEATURE_GATED | ONLY with explicit --quality-integration-v72 flags |
| core/character_memory_v2 | ACTIVE | YES (used by runtime pipeline) |
| core/context_scene_memory | FEATURE_GATED | YES (quality_context_scene_v72 flag) |

---

## 11. Critical Risks

| ID | Severity | Description |
|----|----------|-------------|
| LEGACY_PIPELINE_BRANCH | HIGH | Legacy translation pipeline branch remains production-reachable via explicit `--pipeline=legacy` flag or `NTPE_RUNTIME_PIPELINE=legacy` env var. Three entry points (txt, batch, epub) can activate legacy branch. |

---

## 12. Final Verdict: `P3D1_LEGACY_REACHABLE`

### Reason

Three production-reachable legacy routes exist, all gated by **explicit user opt-in** (`--pipeline=legacy`):

1. TXT legacy branch
2. EPUB legacy branch (delegates to TXT)
3. Batch legacy branch (delegates to TXT)

**These are NOT accidentally reachable** — they require explicit flag. However, per Phase 3D.1 criteria, any production-reachable legacy route = `P3D1_LEGACY_REACHABLE`.

---

## 13. Required Answers to Final Questions

| Question | Answer |
|----------|--------|
| Q1: Single canonical execution path? | YES (runtime pipeline), but legacy branch exists as explicit opt-in |
| Q2: TXT/EPUB use same runtime? | YES - EPUB delegates to TXT runtime pipeline |
| Q3: Production-reachable legacy runtime? | YES - 3 routes via --pipeline=legacy |
| Q4: Duplicate provider path? | NO |
| Q5: Model fallback/override? | NO - configurable but none active |
| Q6: Llama 3.3 triggerable? | NO - only in archive/historical |
| Q7: Minimax triggerable? | NO - only in historical artifacts |
| Q8: Other rejected models? | NO |
| Q9: Nested retry? | NO |
| Q10: Conflicting timeout? | NO |
| Q11: Legacy prompt path? | NO |
| Q12: Legacy context path? | NO |
| Q13: Adaptive/controlled runtime reachable? | NO - feature-gated |
| Q14: M3 end-to-end reachable? | PASS |

---

## 14. Recommended Next Action

**Phase 3D.2 Surgical Cleanup** (NOT Phase 3D.1 scope):

1. Remove legacy pipeline branch from `lts/txt_translation_runtime.py` (lines 1965-2145)
2. Remove `--pipeline` flag and `NTPE_RUNTIME_PIPELINE` handling from `ntpe_production_translate.py`
3. Remove `_pipeline_mode()` function
4. Make runtime pipeline the only path

**Then**: Proceed to **P3E Live Golden Set Validation**

---

## 15. Deliverables

```
artifacts/p3d1_execution_path_audit/
├── P3D1_EXECUTION_PATH_AUDIT_REPORT.json
├── P3D1_EXECUTION_PATH_MATRIX.json
├── P3D1_LEGACY_ROUTE_MATRIX.json
├── P3D1_MODEL_ROUTE_MATRIX.json
├── P3D1_RETRY_TIMEOUT_PATH_MATRIX.json

docs/governance/repository/
└── P3D1_PRODUCTION_EXECUTION_PATH_AUDIT.md
```

---

## 16. Compliance

- ✅ READ-ONLY audit (no modifications)
- ✅ No production code modified
- ✅ No config modified
- ✅ No tests modified
- ✅ No commit / push
- ✅ Historical evidence preserved
- ✅ All artifacts generated

---

**PHASE 3D.1 COMPLETE — STOP**

*Awaiting human decision on Phase 3D.2 cleanup before P3E.*