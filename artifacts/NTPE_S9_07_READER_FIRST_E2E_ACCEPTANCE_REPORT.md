# NTPE S9-07 — Reader-First E2E Acceptance Report

**Task**: `NTPE-S9-07`
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Governance**: no commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## Baseline
- Baseline HEAD: `914a847`
- Actual HEAD: `914a847`

## Audit / Findings Artifacts
- `artifacts/NTPE_S9_07_READER_FIRST_E2E_AUDIT.md`
- `artifacts/NTPE_S9_07_FINDINGS.md`

## E2E Test Files
- `tests/e2e/conftest.py`
- `tests/e2e/test_s9_07_txt_reader_flow.py`
- `tests/e2e/test_s9_07_epub_reader_flow.py`
- `tests/e2e/test_s9_07_failure_recovery.py`

---

## Acceptance Matrix

| Item | Result |
|------|--------|
| TXT Import | PASS |
| TXT Preview | PASS |
| TXT Project Persistence | PASS |
| TXT Normal Translation | PASS |
| TXT Progress | PASS |
| TXT Completion | PASS |
| TXT Output | PASS |
| TXT Open Result | PASS |
| TXT Restart | PASS |
| TXT Recovery | PASS |
| TXT Changed Source | PASS (blocked) |
| TXT Missing Source | PASS (blocked) |
| EPUB Import | PASS |
| EPUB Extraction | PASS |
| EPUB Preview | PASS |
| EPUB Project Persistence | PASS |
| EPUB Translation Entry | **DEFERRED** (canonical gap F1) |
| EPUB Translation | **DEFERRED** |
| EPUB Packaging | **DEFERRED** |
| EPUB Output | **DEFERRED** |
| EPUB Restart | PASS |
| EPUB Project Isolation | PASS |
| Failure UX | PASS |
| Missing Output | PASS |
| Output / Runtime Artifact Separation | PASS |
| Project Isolation | PASS |
| Normal Translation vs Recovery | PASS |
| Recovery vs Retry vs Restart | PASS |
| No Fake Controls | PASS |
| Persistence Across Restart | PASS |

---

## Regression

| Suite | Result |
|-------|--------|
| S9-03 | PASS |
| S9-04 | PASS |
| S9-05 | PASS |
| S9-06 | PASS |
| S8-02/03/04 | PASS |
| Combined (reader_project + e2e + S9 UI + S8) | **151 passed, 1 skipped** |
| Broad `tests/ui` (excl. pre-existing shell hang) | **160 passed, 1 skipped** |
| S9-07 E2E | **27 passed** |

---

## Governance

| Item | Value |
|------|-------|
| Provider Execution | 0 |
| Network Execution | 0 |
| Real Translation | 0 |
| Frozen Runtime Modified | NO |
| Project Schema Changed | NO |
| Second Persistence | NO |
| Automatic Source Rebind | NO |
| Retry Added | NO |
| Restart Added | NO |
| Glossary | NOT IMPLEMENTED |
| Root Hygiene | PASS |
| Git Commit / Push / Tag | NO |

---

## Pre-existing Issues
- `tests/ui/test_translation_studio_shell.py` `window.close()` hang — PRE-EXISTING / OUT-OF-SCOPE.
- `tests/literary/outputs/PS-03/README.md` deleted + 3 literary residual files modified — PRE-EXISTING / UNTOUCHED.

## Acceptance Gaps
- **F1 (DEFERRED)**: EPUB translation entry cannot complete because canonical EPUB extraction does not
  populate chapter body offsets required by canonical chunking. Pre-existing capability gap; not an S9-07
  regression; frozen boundary not modified; no fake route added.

## Stop Conditions
- NONE

---

## FINAL: PASS (with EPUB translation DEFERRED, per §39)

TXT reader journey is fully accepted end-to-end (import → project → translation → progress → completion →
output → restart → recovery → blocked-on-source-change/missing), offline and deterministic.
EPUB import/extraction/preview/persistence/isolation accepted; EPUB translation entry formally DEFERRED
with a recorded, classified capability gap.
