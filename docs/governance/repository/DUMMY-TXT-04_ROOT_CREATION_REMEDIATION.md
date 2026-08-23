# DUMMY-TXT-04 Root Creation Remediation

**Repository:** D:\Python\NTPE
**Baseline Commit:** 93d7498e051643f1f6cfd6caf8fb72a07a866c73
**Remediation Date:** 2026-08-23
**Status:** PASS — Root `dummy.txt` no longer created by tests

---

## 1. Original Creator Chain (from DUMMY-TXT-03)

| Component | Detail |
|-----------|--------|
| **Creator File** | `core/glossary.py` |
| **Creator Function** | `Glossary.load()` line 15 |
| **Creator Code** | `self.path.write_text("정태의=鄭泰義\n카일=凱爾\n", encoding="utf-8")` |
| **Trigger Location** | `tests/series/test_batch5_4.py:1031` |
| **Trigger Test** | `TestFrozenComponentIntegration.test_glossary_adapter_integration` |
| **Trigger Code** | `g = Glossary(Path("dummy.txt"))  # Won't be used since we override` |
| **Batch** | Batch 5.4 (deliver series glossary) |
| **Commit** | `1d9257b P0 Stage 5 Batch 5.4: deliver series glossary` |

---

## 2. Remediation

### Files Modified
- `tests/series/test_batch5_4.py`

### Change Detail

**File:** `tests/series/test_batch5_4.py`
**Method:** `TestFrozenComponentIntegration.test_glossary_adapter_integration`

```diff
-        from core.glossary import Glossary
-        g = Glossary(Path("dummy.txt"))  # Won't be used since we override
+        from core.glossary import Glossary
+        g = Glossary(tmp_path / "dummy.txt")  # Use temp path, won't be used since we override
```

**Rationale:** The test only needs a `Glossary` instance to override its `terms` dictionary. The file path is never actually used since `g.terms` is immediately replaced. Using `tmp_path` (pytest fixture) ensures no filesystem side effects at repository root.

---

## 3. Validation Results

| Check | Result |
|-------|--------|
| `dummy.txt` at root before test | False |
| `dummy.txt` at root after test | False |
| Batch 5.4 tests | **43 passed** |
| Batch 5.1 tests | **47 passed** |
| Batch 5.2 tests | **39 passed** |
| Batch 5.3 tests | **81 passed** |
| Batch 5.5 tests | **65 passed** |
| Batch 5.6 tests | **27 passed** |
| Batch 5.7 tests | 275 passed, 6 failed (pre-existing, unrelated) |
| `ntpe_validate.py` | **PASS WITH WARNINGS** (1 pre-existing warning) |
| `python -m compileall core/` | **PASS** (2942 files, 0 errors) |
| `git diff --check` | **Clean** (only pre-existing CRLF warnings) |
| Root Hygiene | **0 new violations** |
| Protected worktree | **Unmodified** (only pre-existing CRLF changes) |

---

## 4. Other Patterns Checked

| Pattern | Found | Status |
|---------|-------|--------|
| `Glossary(Path("dummy.txt"))` | Only in `test_batch5_4.py:1031` | **Fixed** |
| `Glossary("dummy.txt")` | None | — |
| Other `Glossary` with relative path creating root files | None in current test suite | — |

---

## 5. Pre-existing Issues (Unrelated)

### test_batch5_7_orchestration.py — 6 Failed Tests

| Failed Test | Error Type |
|-------------|------------|
| `test_translate_txt_with_series_context_none` | `AttributeError: 'NoneType' object has no attribute 'get'` |
| `test_series_knowledge_reaches_mergedruntime` | `AssertionError: Character domain missing from MergedRuntime` |
| `test_mergedruntime_reaches_promptbuilder` | `AssertionError: Series character missing from Character section` |
| `test_cross_series_isolation_promptbuilder` | `AssertionError: assert '' != ''` (knowledge hash) |
| `test_checkpoint_resume_e2e` | `AssertionError: assert 'promoted' == 'completed'` |
| `test_invalid_checkpoint_rejection` | `ValidationError: Series not found: wrong_series_id` |

**Note:** These failures are in `test_batch5_7_orchestration.py` and relate to runtime integration/knowledge population, **not** the `dummy.txt` issue. They exist independently of this remediation.

---

## 6. Acceptance Criteria Met

```
DUMMY-TXT-04
├─ Root dummy.txt after test       = ABSENT ✅
├─ Batch 5.4 tests                 = PASS ✅
├─ Series tests                    = PASS ✅ (except pre-existing 5.7 failures)
├─ Production Glossary behavior    = UNCHANGED ✅
├─ Frozen contracts                = UNCHANGED ✅
├─ Root Hygiene                    = 0 new violations ✅
├─ Unknown files                   = 0 ✅
└─ Protected worktree              = UNTOUCHED ✅
```

---

## 7. STOP Condition

**STOP-03-01 — CREATOR = IDENTIFIED AND REMEDIATED**

- ✅ Specific file: `core/glossary.py`
- ✅ Specific function: `Glossary.load()` (line 15)
- ✅ Specific caller: `tests/series/test_batch5_4.py::TestFrozenComponentIntegration::test_glossary_adapter_integration` (line 1031)
- ✅ Specific execution path: Test run → Glossary instantiation → load() → file creation
- ✅ **Remediation applied:** Test now uses `tmp_path` fixture, no root filesystem side effect

---

## 8. Protected Worktree Verification

| Check | Result |
|-------|--------|
| `git status --short` at start | 22 tracked changes (pre-existing), 12 untracked |
| `git status --short` at end | Same + `tests/series/test_batch5_4.py` (modified by this fix) |
| Protected files modified | Only pre-existing CRLF normalization artifacts |
| New root files created | **None** |

---

## 9. No Commit / Push

Per requirements, this remediation is delivered as working-tree changes only. No commit or push performed.

---

*End of DUMMY-TXT-04 Root Creation Remediation Report.*