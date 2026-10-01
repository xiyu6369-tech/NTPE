# NTPE S6-01 EPUB CLI Dispatch Repair Report

**Date**: 2026-09-26
**Baseline Commit**: 942650d (chore(repo): clean up S5 diagnostic artifacts)
**Branch**: main
**origin/main**: 942650d

---

## 1. Baseline Verification

| Item | Expected | Actual | Status |
|------|----------|--------|--------|
| HEAD | 942650d | 942650d | ✅ PASS |
| origin/main | 942650d | 942650d | ✅ PASS |
| Branch | main | main | ✅ PASS |
| 4 Existing Modifications | Preserved | Preserved | ✅ PASS |

---

## 2. Modified Files

**Single file modified**: `ntpe_production_translate.py`

### Exact Change

```diff
--- a/ntpe_production_translate.py
+++ b/ntpe_production_translate.py
@@ -1118,6 +1118,8 @@ def main(argv: Iterable[str] | None = None) -> int:
         return run_txt(args)
     if args.command == "batch":
         return run_batch(args)
+    if args.command == "epub":
+        return run_epub(args)
     parser.print_help()
     return 1
```

**Location**: Lines 1121-1122 (added after `batch` command handler, before fallback)

---

## 3. CLI Dispatch Verification

### Test Command
```bash
python -c "
import sys
sys.path.insert(0, 'D:/Python/NTPE')
from ntpe_production_translate import main
sys.argv = ['ntpe_production_translate.py', 'epub', 'artifacts/test.epub', 'output', '--dry-run', '--no-progress']
result = main()
print('Exit code:', result)
"
```

### Result
```
NTPE Production EPUB Translation
==================================
Input: D:\Python\NTPE\artifacts\test.epub
Output: D:\Python\NTPE\output
EPUB intake not eligible for translation: manual_review_required
  Warning: Language detection uncertain: mixed
Exit code: 1
```

### Verification
- ✅ `epub` command correctly dispatched from `main()`
- ✅ `run_epub(args)` executed (printed "NTPE Production EPUB Translation" banner)
- ✅ No second EPUB translation route created
- ✅ Existing `run_epub()` function reused (no duplication)
- ✅ Exit code 1 returned (expected for `manual_review_required` intake status)

---

## 4. S5 Regression Test Results

### S5-A: EPUB Packaging Tests
```
tests/contract/test_s5_epub_packaging.py: 37 passed, 2 warnings
```
✅ **37/37 PASS**

### S5-B: EPUB Structure Tests
```
tests/contract/test_s5b_epub_structure.py: 39 passed, 3 warnings
```
✅ **39/39 PASS**

### S5-C: EPUB Reference Integrity Tests
```
tests/contract/test_s5c_reference_integrity.py: 21 passed, 1 warning
```
✅ **21/21 PASS**

---

## 5. Existing Modifications Preservation

All 4 pre-existing working tree modifications remain intact:

| File | Status |
|------|--------|
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | ✅ Modified (preserved) |
| `tests/literary/outputs/Regression_History.json` | ✅ Modified (preserved) |
| `tests/literary/outputs/Regression_History.md` | ✅ Modified (preserved) |
| `tests/ui/mock_translation_runtime.py` | ✅ Modified (preserved) |

---

## 6. Root Hygiene

| Check | Result |
|-------|--------|
| No root `.py` files created | ✅ PASS |
| No root `.ps1` files created | ✅ PASS |
| No root `.bat` files created | ✅ PASS |
| No root `.json` files created | ✅ PASS |
| No root `.txt` files created | ✅ PASS (test_input.txt pre-existed) |
| No root `.log` files created | ✅ PASS |
| No new scratch files in root | ✅ PASS |
| All artifacts in `artifacts/` | ✅ PASS |

---

## 7. Governance Compliance

| Requirement | Compliance |
|-------------|------------|
| No provider modification | ✅ |
| No model modification | ✅ (model remains `meta/llama-3.2-90b-vision-instruct`) |
| No prompt modification | ✅ |
| No TranslationRuntime modification | ✅ |
| No TranslationEngine modification | ✅ |
| No EPUB packager modification | ✅ |
| No EPUB contract modification | ✅ |
| No language detector modification | ✅ |
| No UI modification | ✅ |
| No S6-02 through S6-10 modifications | ✅ |
| No LTS/TE architecture changes | ✅ |
| No `run_epub()` reimplementation | ✅ (existing function reused) |
| No test cleanup | ✅ |
| No artifacts cleanup | ✅ |
| No existing feature deletion | ✅ |
| No commit | ✅ |
| No push | ✅ |
| No tag | ✅ |

---

## 8. Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| `main()` dispatches `epub` | ✅ |
| `epub` command enters existing `run_epub()` | ✅ |
| No second EPUB translation route created | ✅ |
| No provider modification | ✅ |
| No model modification | ✅ |
| No prompt modification | ✅ |
| No EPUB packager modification | ✅ |
| No UI modification | ✅ |
| No S6-02～S6-10 modifications | ✅ |
| S5-A = 37/37 PASS | ✅ |
| S5-B = 39/39 PASS | ✅ |
| S5-C = 21/21 PASS | ✅ |
| 4 existing modifications preserved | ✅ |
| No root scratch files | ✅ |
| No existing features deleted | ✅ |
| No commit | ✅ |
| No push | ✅ |
| No tag | ✅ |

---

## 9. Summary

**Result**: **S6_01_EPUB_CLI_DISPATCH_REPAIR_PASS**

- **Baseline HEAD**: 942650d
- **Files Modified**: 1 (`ntpe_production_translate.py`)
- **Lines Changed**: +2 (addition only)
- **S5-A Tests**: 37/37 PASS
- **S5-B Tests**: 39/39 PASS
- **S5-C Tests**: 21/21 PASS
- **Existing Modifications**: 4/4 preserved
- **Commit**: NO
- **Push**: NO
- **Tag**: NO

The minimal CLI dispatch fix is complete. The `epub` command now correctly routes through `main()` → `run_epub()` using the existing EPUB translation pipeline.