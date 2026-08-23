# DUMMY-TXT Incident Closure

**Repository:** D:\Python\NTPE
**Baseline Commit:** 93d7498e051643f1f6cfd6caf8fb72a07a866c73
**Closure Date:** 2026-08-23
**Status:** CLOSED

---

## 1. Incident Summary

| Field | Value |
|-------|-------|
| Incident ID | DUMMY-TXT |
| Status | **CLOSED** |
| Root Cause | Test fixture instantiated `Glossary` with repository-relative `Path("dummy.txt")` |
| Creator | `core/glossary.py` — `Glossary.load()` line 15 |
| Trigger | `tests/series/test_batch5_4.py::TestFrozenComponentIntegration::test_glossary_adapter_integration` (line 1031) |
| Remediation | Use `pytest` `tmp_path` fixture instead of repository-relative root path |
| Verification | DUMMY-TXT-05 full `tests/series/` regression |
| Final State | `dummy.txt` **ABSENT** after regression |

---

## 2. Discovery

The `dummy.txt` file was discovered at repository root during routine hygiene audit. Initial investigation (DUMMY-TXT-02) could not attribute creator. Deep trace (DUMMY-TXT-03) identified the complete causal chain.

---

## 3. Root Cause

```python
# core/glossary.py, line 15
if not self.path.exists():
    self.path.parent.mkdir(parents=True, exist_ok=True)
    self.path.write_text("정태의=鄭泰義\n카일=凱爾\n", encoding="utf-8")
```

The `Glossary` class auto-creates a default Korean glossary file if the provided path doesn't exist. This is correct production behavior for user-facing glossary files, but the test used a repository-relative path.

---

## 4. Creator Attribution

| Component | Detail |
|-----------|--------|
| **File** | `core/glossary.py` |
| **Function** | `Glossary.load()` (line 15) |
| **Code** | `self.path.write_text("정태의=鄭泰義\n카일=凱爾\n", encoding="utf-8")` |
| **Caller File** | `tests/series/test_batch5_4.py` |
| **Caller Test** | `TestFrozenComponentIntegration.test_glossary_adapter_integration` |
| **Caller Line** | 1031 |
| **Original Code** | `g = Glossary(Path("dummy.txt"))  # Won't be used since we override` |

---

## 5. P0_STAGE5 / Series Relationship

The incident is **causally linked** to P0_STAGE5 Batch 5.4:

```
P0_STAGE5 Batch 5.4 implements Series Glossary
    ↓
test_batch5_4.py added with TestFrozenComponentIntegration
    ↓
test_glossary_adapter_integration instantiates Glossary(Path("dummy.txt"))
    ↓
Glossary.__init__ calls load()
    ↓
load() checks if file exists → creates with default content if not
    ↓
Default content: "정태의=鄭泰義\n카일=凱爾\n" (Korean test glossary terms)
    ↓
dummy.txt created at repository root
```

**Evidence:**
- **P0_STAGE5 → Series:** PROVEN (Batch 5.4 implements Series Glossary)
- **Series → dummy.txt:** PROVEN (via Batch 5.4 test execution)

---

## 6. Remediation

**File:** `tests/series/test_batch5_4.py`  
**Line:** 1031  
**Method:** `TestFrozenComponentIntegration.test_glossary_adapter_integration`

```diff
-        from core.glossary import Glossary
-        g = Glossary(Path("dummy.txt"))  # Won't be used since we override
+        from core.glossary import Glossary
+        g = Glossary(tmp_path / "dummy.txt")  # Use temp path, won't be used since we override
```

**Rationale:** The test only needs a `Glossary` instance to override its `terms` dictionary. The file path is never actually used since `g.terms` is immediately replaced. Using `tmp_path` (pytest fixture) ensures no filesystem side effects at repository root.

---

## 7. DUMMY-TXT-05 Verification

### Full Series Regression
```
Command: python -m pytest tests/series/
Collected: 287
Passed: 281
Failed: 6 (pre-existing)
Skipped: 0
Errors: 0
```

### Failed Tests (All Pre-existing)
| Test | Error Type |
|------|------------|
| `test_translate_txt_with_series_context_none` | `AttributeError: 'NoneType' object has no attribute 'get'` |
| `test_series_knowledge_reaches_mergedruntime` | `AssertionError: Character domain missing from MergedRuntime` |
| `test_mergedruntime_reaches_promptbuilder` | `AssertionError: Series character missing from Character section` |
| `test_cross_series_isolation_promptbuilder` | `AssertionError: assert '' != ''` (knowledge hash) |
| `test_checkpoint_resume_e2e` | `AssertionError: assert 'promoted' == 'completed'` |
| `test_invalid_checkpoint_rejection` | `ValidationError: Series not found: wrong_series_id` |

**Analysis:** All 6 failures are in `test_batch5_7_orchestration.py`, identical to DUMMY-TXT-04 verification. None related to `dummy.txt` or the remediation.

### Key Results
- `dummy.txt` after regression: **ABSENT**
- Root filesystem side effect: **NONE**
- Protected worktree: **UNCHANGED**

---

## 8. Governance Assessment

### Root Hygiene Policy
**Sufficient.** The existing Root Hygiene policy already prohibits root-level test artifacts. This was a test fixture implementation bug, not a policy gap.

### Governance Change Required
**NO** — No governance rule modification needed. The violation was a test implementation error.

### Recommendation
> Tests that create writable filesystem fixtures MUST use `pytest tmp_path` / temporary workspace rather than repository-root relative paths.

### Key Principle
> **.gitignore is NOT a remediation for filesystem side effects.**
>
> A test that creates an unwanted root-level file remains a filesystem hygiene violation even if the file is ignored by Git. The correct remediation is to **eliminate creation**, not hide generated file.

---

## 9. Protected Worktree Verification

| File | Status |
|------|--------|
| `artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json` | Unmodified |
| `artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json` | Unmodified |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | Unmodified |
| `tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json` | Unmodified |
| `tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json` | Unmodified |
| `tests/literary/outputs/Regression_History.json` | Unmodified |
| `tests/literary/outputs/Regression_History.md` | Unmodified |

**Status:** **UNCHANGED** (only pre-existing CRLF normalization artifacts)

---

## 10. Known Pre-existing Failures

The following 6 failures in `tests/series/test_batch5_7_orchestration.py` are **pre-existing** and **unrelated** to this incident:

| Test | Error |
|------|-------|
| `test_translate_txt_with_series_context_none` | `AttributeError: 'NoneType' object has no attribute 'get'` |
| `test_series_knowledge_reaches_mergedruntime` | `AssertionError: Character domain missing from MergedRuntime` |
| `test_mergedruntime_reaches_promptbuilder` | `AssertionError: Series character missing from Character section` |
| `test_cross_series_isolation_promptbuilder` | `AssertionError: assert '' != ''` (knowledge hash) |
| `test_checkpoint_resume_e2e` | `AssertionError: assert 'promoted' == 'completed'` |
| `test_invalid_checkpoint_rejection` | `ValidationError: Series not found: wrong_series_id` |

**Do NOT classify these as DUMMY-TXT regression.**

---

## 11. Final Closure Decision

```
DUMMY-TXT-06
│
├─ DUMMY-TXT-03 evidence consistent       PASS
├─ DUMMY-TXT-04 evidence consistent       PASS
├─ DUMMY-TXT-05 evidence consistent       PASS
├─ Creator attribution                    CONFIRMED
├─ Root cause                             CONFIRMED
├─ Remediation                            APPLIED AND VERIFIED
├─ Full regression                        VERIFIED
├─ dummy.txt regeneration                 NONE
├─ Governance impact                      ASSESSED - NO CHANGE REQUIRED
├─ Protected Worktree                     UNCHANGED
├─ Production code                        UNCHANGED
├─ Frozen contracts                       UNCHANGED
├─ Closure report                         CREATED
└─ Incident status                        CLOSED
```

**Final Verdict:** **DUMMY-TXT INCIDENT = CLOSED**  
**Root Side Effect = REMEDIATED**  
**Regression = PASS**

**Note:** 6 pre-existing Series failures remain outside this incident.

---

## 12. Deliverables

1. **`artifacts/DUMMY-TXT-06_Incident_Closure_Report.json`** — Complete JSON closure report
2. **`docs/governance/repository/DUMMY-TXT-06_DUMMY_TXT_INCIDENT_CLOSURE.md`** — This Markdown governance document

---

## 13. No Commit / Push

Per requirements, closure delivered as working-tree changes only.

**COMMIT = NO**  
**PUSH = NO**

---

*End of DUMMY-TXT Incident Closure.*