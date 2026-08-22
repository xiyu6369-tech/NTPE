# RM-7.3.1 — Entity Normalization Runtime Integration Canary Report

**Generated:** 2026-08-17T21:36:43
**Version:** rm-7.3.1
**Status:** COMPLETED

---

## Objective

驗證完整鏈路：
```
Knowledge Evolution
    ↓
Entity Resolver (RM-7.2)
    ↓
Entity Normalization (RM-7.3)
    ↓
Prompt Runtime
    ↓
Translation Runtime
    ↓
Translation Engine
```

## Canary Input

| Item | Value |
|------|-------|
| Source | `tests/fixtures/rm73_entity_canary/novel_sample.txt` |
| Size | 5837 bytes / 2537 chars |
| Description | Korean novel excerpt with entity normalization test cases |
| Direction | ko → zh-TW (literary profile) |

---

## Execution

| Metric | Runtime | Legacy |
|--------|---------|--------|
| Completion | **FAIL** | **FAIL** |
| Elapsed | 0.2s | 0.28s |
| Chunks | 0 | 0 |
| Provider Requests | 9 | 0 |

---

## Entity Normalization Pipeline

| Step | Count |
|------|-------|
| Entities Extracted | 25 |
| Entities Resolved | 25 |
| Entities Normalized | 25 |
| Conflicts Detected | 0 |

---

## Entity Detection Verification

| Check | Result | Detail |
|-------|--------|--------|
| All sources detected | **PASS** | 25 entities detected |

### Detail

- 정태의: ✓ (detected: True, canonical: 鄭泰義, expected: 鄭泰義, level: USER, form: FULL_NAME, translation: 鄭泰義)
- 태의: ✓ (detected: True, canonical: 鄭泰義, expected: 泰義, level: USER, form: GIVEN_NAME, translation: 泰義)
- 정 씨: ✓ (detected: True, canonical: 鄭泰義, expected: 鄭先生, level: USER, form: FORMAL, translation: 鄭先生)
- 태의야: ✓ (detected: True, canonical: 鄭泰義, expected: 泰義啊, level: USER, form: INTIMATE, translation: 泰義啊)


---

## Prompt Injection Verification

| Check | Result |
|-------|--------|
| Entity Identity section present | **True** |
| Source '정태의' included | **True** |
| Canonical '鄭泰義' included | **True** |
| FULL form included | **True** |
| GIVEN form included | **True** |
| INTIMATE form included | **True** |
| Rule 'Do not expand given name' | **True** |

Overall: **PASS**

---

## Translation Output Verification

| Check | Result |
|-------|--------|
| No wrong intimate form (鄭泰義啊) | **False** |
| Correct intimate form (泰義啊) | **False** |
| Correct formal form (鄭先生/鄭泰義先生) | **False** |
| Correct full form (鄭泰義) | **False** |
| Correct given form (泰義) | **False** |

Overall: **SKIP**

---

## Provider Request Count Verification

| Pipeline | Provider Calls |
|----------|---------------|
| Runtime | 9 |
| Legacy | 0 |
| Δ | 9 |

> Entity Normalization Layer is offline-only. No additional provider calls introduced.

Overall: **FAIL**

---

## Legacy Compatibility

| Check | Result |
|-------|--------|
| Legacy pipeline works | **FAIL** |
| Legacy chunks | 0 |
| Legacy provider calls | 0 |

---

## Strict Constraint Compliance

RM-7.3.1 prohibits modification to these modules:

| Module | Modified? |
|--------|----------|
| `core/translation_engine/` | NO |
| `core/prompt_runtime/` | NO |
| `core/knowledge_runtime/` | NO |
| `core/runtime_session/` | NO |
| `core/runtime_checkpoint/` | NO |
| `core/runtime_trace/` | NO |
| `provider/` | NO |

Only test fixtures, canary tools, and documentation were created.

---

## Decision

### RM-7.3.1 Entity Normalization Runtime Integration Canary

**FAIL

**Failures:** runtime pipeline failed; legacy pipeline failed; provider count constraint violated; legacy compatibility broken.

**Production Readiness: Do NOT proceed until issues are resolved.**


---

## Validation

```powershell
python ntpe_validate.py
```

```
ALL PASS
```

```powershell
python -m compileall .\core
```

```
0 errors
```

```powershell
git diff --check
```

```
PASS
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| Runtime Output | `artifacts/rm7_entity_canary/runtime/` |
| Legacy Output | `artifacts/rm7_entity_canary/legacy/` |
| Entity Resolution | `artifacts/rm7_entity_canary/entity_resolution.json` |
| Normalized Prompt | `artifacts/rm7_entity_canary/normalized_prompt.json` |
| Translation Output | `artifacts/rm7_entity_canary/translation_output.txt` |
| Consistency Report | `artifacts/rm7_entity_canary/consistency_report.json` |
| Test Fixture | `tests/fixtures/rm73_entity_canary/novel_sample.txt` |
| Canary Runner | `tools/canary/run_entity_canary.py` |

