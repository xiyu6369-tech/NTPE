# Phase 3C — M3 Production Migration Readiness & Pre-Migration Audit

**Status**: `P3C_READY_FOR_MIGRATION`
**Baseline**: `af5cbc091424849134c28ef931ce78d31ea0dc7d`
**Target Model**: `meta/llama-3.2-90b-vision-instruct`
**Date**: 2026-08-30

---

## 1. Baseline Lock Verification

```powershell
git rev-parse HEAD
# af5cbc091424849134c28ef931ce78d31ea0dc7d

git status --short
# (clean - only untracked Phase 3A/3B artifacts)

git diff --stat
# (no changes)

git diff --name-status
# (no changes)
```

✅ **Baseline integrity verified**: HEAD = af5cbc0, working tree clean

---

## 2. Candidate Lock

**唯一 migration candidate**: `meta/llama-3.2-90b-vision-instruct` (M3)

- Provider: NVIDIA
- P3B Results: 100% completion, 0 timeouts, Quality 80/100, Avg Latency 19.2s
- No other models evaluated in Phase 3C/3D

---

## 3. RI Preservation Invariants (7/7 PASS)

| RI | Description | Status |
|----|-------------|--------|
| RI-01 | HTTP 408 Non-Retryable Classification | ✅ PASS |
| RI-02 | Dynamic Retry Config Parameters | ✅ PASS |
| RI-03 | Dynamic Retry Parameter Usage | ✅ PASS |
| RI-04 | Retry Config Propagation from Metadata | ✅ PASS |
| RI-05 | Balanced Profile Attempts 2 → 3 | ✅ PASS |
| RI-06 | Partial Translation Handling / `incomplete` | ✅ PASS |
| RI-07 | Retry Metadata + Enhanced Summary | ✅ PASS |

All RI invariants preserved in `core/translation_engine/provider_runtime.py`

---

## 4. EPUB Pipeline Preservation

✅ **EPUB pipeline intact** — No model-specific changes in:
- `core/adapters/epub_extraction_boundary.py` — Pure extraction, no model dependency
- `core/translation_release/exporters/epub_exporter.py` — Pure packaging, no model dependency
- EPUB intake → extraction → translation → packaging chain unchanged

---

## 5. Model Reference Inventory Summary

| Classification | Count | Description |
|----------------|-------|-------------|
| **MIGRATE** | 32 | Production config/code requiring model change |
| **TEST_UPDATE** | 16 | Test expectations requiring update |
| **DOCUMENTATION_UPDATE** | 8 | Documentation references requiring update |
| **HISTORICAL_EVIDENCE** | 28 | P3A/P3B/Pre-Minimax/TIC artifacts — **PRESERVED AS-IS** |
| **NO_CHANGE** | 11 | Tooling already using M3 or comparing models |
| **TOTAL** | 95 | All references catalogued |

---

## 6. Critical Historical Evidence Protection

**All historical artifacts preserved unchanged:**

- P3A Model Compatibility Probe reports
- P3A.1 Reconstructed Baseline Closure
- P3A.2 DeepSeek V4 Compatibility Probe
- P3B Model Comparison reports (M3 vs M4)
- Pre-Minimax baseline recovery/reconstruction reports
- TIC Batch 2/4/5 failure corpus indices
- All archive/ stage tests

**Rule enforced**: Historical evidence MUST retain original model IDs. No retroactive substitution.

---

## 7. Configuration Audit

All active configuration entries for NVIDIA provider updated to target M3:

| Config File | Entry | Current | Target |
|-------------|-------|---------|--------|
| `config/provider_config.json` | providers.nvidia.default_model | llama-3.3-70b | llama-3.2-90b-vision |
| `config/models.json` | nvidia.default + models[] | llama-3.3-70b | llama-3.2-90b-vision |
| `config/launcher_product_defaults.json` | model_id | llama-3.3-70b | llama-3.2-90b-vision |
| `config/default_config.json` | model | llama-3.3-70b | llama-3.2-90b-vision |
| `core/config.py` | DEFAULT_CONFIG.model | llama-3.3-70b | llama-3.2-90b-vision |

---

## 8. Hard-Code Audit

| Check | Result |
|-------|--------|
| Llama 3.3 hard-coded in production | ⚠️ **FOUND** (32 locations — all in allowlist) |
| Minimax hard-coded in production | ✅ NONE |
| Model-specific prompt branch | ✅ NONE |
| Model-specific retry branch | ✅ NONE |
| Model-specific output parser | ✅ NONE |
| Model-specific context branch | ✅ NONE |

All Llama 3.3 references in production code are catalogued in allowlist for migration.

---

## 9. Provider Compatibility Audit

✅ **M3 uses existing NVIDIA provider path**
- Endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`
- Model ID propagation: Standard OpenAI-compatible `model` field
- Request payload: Unchanged
- Response parsing: Unchanged
- Error classification: Preserved (RI-01)

No provider abstraction modifications required.

---

## 10. Timeout/Retry Audit

✅ **Baseline runtime settings preserved**
- M3 avg latency: 19.2s (well within 180s timeout)
- No timeout modification required
- RI-01 through RI-07 unchanged
- Conservative retry strategy maintained: 2 attempts, 10s base backoff

---

## 11. Prompt Audit

✅ **No prompt modification required**
- Baseline prompt: Existing NTPE literary translation prompt
- M3 works with baseline prompt (P3B validated)
- No M3-specific instructions added
- No model-specific workarounds
- Translation contract unchanged

---

## 12. Test Audit

**Tests requiring TEST_UPDATE (16):**
- 2 unit tests
- 14 integration tests

**Tests preserved as HISTORICAL_EVIDENCE (not modified):**
- Archive stage tests
- Beta stage tests
- Smoke tests with historical assertions
- P3A/P3B tool tests

---

## 13. Rollback Plan

| Item | Detail |
|------|--------|
| Baseline Commit | `af5cbc091424849134c28ef931ce78d31ea0dc7d` |
| Checkpoint Method | `git tag` (immutable) |
| Restoration Target | Working tree + active model restored |
| Verification | `ntpe_validate.py`, unit tests, RI verification |

Checkpoint created **before Phase 3D migration**.

---

## 14. Phase 3C Deliverables

```
artifacts/p3c_migration_readiness/
├── P3C_M3_MIGRATION_READINESS_REPORT.json
├── P3C_MODEL_REFERENCE_INVENTORY.json
├── P3C_MODEL_MIGRATION_ALLOWLIST.json

docs/governance/repository/
└── P3C_M3_MIGRATION_READINESS.md
```

---

## 15. Phase 3C Final Gate

| Gate | Status |
|------|--------|
| Baseline Integrity | ✅ PASS |
| Model Reference Inventory Complete | ✅ PASS |
| Migration Allowlist Complete | ✅ PASS |
| No Unknown Production References | ✅ PASS |
| RI-01–RI-07 Preservation | ✅ PASS (7/7) |
| EPUB Preservation | ✅ PASS |
| Provider Path Verified | ✅ PASS |
| Prompt Unchanged | ✅ PASS |
| No Model-Specific Workaround | ✅ PASS |
| Rollback Strategy Defined | ✅ PASS |
| Historical Evidence Protected | ✅ PASS |

---

## 16. Final Verdict

### `P3C_READY_FOR_MIGRATION`

Phase 3C complete. All gates pass. Phase 3D migration authorized per allowlist.

---

## 17. Phase 3D Preview

Phase 3D will execute **only** the 56 allowlisted changes:
- 32 MIGRATE (production config/code)
- 16 TEST_UPDATE (test expectations)
- 8 DOCUMENTATION_UPDATE (docs)

**No other files modified. No scope expansion.**

Post-migration validation gates:
- RI Integrity Gate (7/7)
- EPUB Gate
- Unit Test Gate (0 unexpected failures)
- Provider Smoke Gate
- Golden Set Regression Gate (vs P3B baseline: 100% completion, 0 timeout, Q80, 19.2s)
- Repository Scope Audit
- Model Reference Final Audit

Only if **ALL GATES PASS** → migration commit created (NO PUSH).