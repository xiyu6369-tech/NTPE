# NTPE S12-07 — Glossary EPUB Real-Adapter Reader-First E2E Re-verification

Verification / closure only. No production repair. Closes the S12-04 EPUB block that
S12-06 unblocked, with a persisted EPUB produced and freshly read back.

## 0. Baseline

| Metric | Value |
|--------|-------|
| Baseline HEAD | `83e34f064c5dc5b2bc9d664813f2c9d55ac83fd9` |
| Actual HEAD | `83e34f0` + this commit |
| origin/main (before) | `83e34f0` |
| Branch | `main` |

Verified with `git status --short`, `git branch --show-current`, `git rev-parse HEAD`,
`git rev-parse origin/main`. No reset/clean/stash/restore.

## 1. Result summary

```text
UI Import                 : PASS
Project Persistence       : PASS
Restart                   : PASS
EPUB Option Binding       : PASS
Glossary Hash             : PASS
Real EPUB Adapter         : PASS
Offset Validation         : PASS
Glossary Terminology      : PASS (production-generated)
Real Packaging            : PASS
Persisted EPUB            : PASS
Fresh Read-back           : PASS
Chapter Identity          : PASS
Spine Order               : PASS
Non-Linear Semantics      : PASS
TOC                       : PASS
Resource Mapping          : PASS
Replace                   : PASS
Detach / No-glossary      : PASS
Corrupt Glossary          : PASS
Recovery                  : PASS (existing contract re-run)
Determinism               : PASS
Provider / Network / Real Translation : 0 / 0 / 0
Production Files Modified : NO
```

## 2. Real vs stubbed boundary

Real: `ProjectPage`, `ReaderProjectManager`, glossary backend/snapshot, EPUB extraction,
intake, `EpubTranslationInput`, `EpubTranslationChunk`, `chunk_epub_translation_input`,
`validate_epub_translation_chunk`, `translate_epub_translation_input`,
`build_epub_reader_chapter_map_with_metadata`, `pack_epub_resource_aware`, filesystem
write, fresh `zipfile` read-back.

Stubbed (external model execution boundary only): `RuntimeOrchestrator.execute` returns a
deterministic echo. The provider, network and real model are never invoked
(`provider = 0`, `network = 0`, `real translation = 0`). The EPUB adapter / chunking /
validation / packaging are **not** replaced.

## 3. Fixture

Deterministic EPUB: 3 chapters (`Chapter One/Two/Three`, spine `ch1/ch2/ch3`), spine
linear semantics `yes / no / yes`, one referenced image resource (`pic.png`, referenced
from `ch1.xhtml`), and project glossary term `TEST_TERM_A` (plus `정태의`) placed in
`ch2.xhtml`. No heading element in the chapter body so the packager's paragraph mapping
aligns cleanly.

## 4. Core E2E evidence

```text
ProjectPage -> _on_glossary_import (mocked file chooser only)
-> ReaderProject.glossary persisted (content_hash, term_count=2, active)
-> fresh ReaderProjectManager + ProjectPage reload: same hash / term_count / active
-> page._on_translate -> canonical EpubTranslationOptions
   glossary_path = Project-owned snapshot (NOT the user file), glossary_hash = content_hash
-> real translate_epub_translation_input (validator passes; S12-06 repair)
-> real pack_epub_resource_aware -> <source-adjacent>/output/epub_translation/.../book_zh.epub
-> project.output.artifact_path persisted, artifact_kind="epub", available=True
-> fresh zipfile read-back
```

Read-back assertions (`test_s12_07_reader_first_real_adapter_e2e`):

```text
chapters present            : ch1.xhtml, ch2.xhtml, ch3.xhtml, nav.xhtml
spine idrefs                : ["nav", "ch1", "ch2", "ch3"]
non-linear preserved        : <itemref idref="ch2" linear="no"/>
resource mapping            : pic.png present; ch1.xhtml references src="pic.png"
terminology (ch2)           : 測試詞彙甲 present, 鄭泰義 present, TEST_TERM_A ABSENT
no cross-chapter leakage    : 測試詞彙甲 absent from ch1.xhtml / ch3.xhtml
```

The echo runtime returns the **source** text unchanged; the only code that introduces
`測試詞彙甲` is the canonical `_apply_locked_dictionary` loaded from the Project-owned
glossary snapshot. No test-side `.replace` / manual translation / fabricated packaging
(is proven by the no-glossary contrast below).

## 5. Feature-off contrast, replace, corrupt

| Test | Evidence |
|------|----------|
| Detach then launch | `glossary_path is None`, `glossary_hash is None`; `TEST_TERM_A` survives untranslated, `測試詞彙甲` absent — proves the glossary effect is production-generated, not test-simulated |
| Replace A→B | new glossary hash used; final EPUB contains `測試詞彙乙`, not `測試詞彙甲`, no source term |
| Corrupt active glossary | launch blocked, `_RealEpubRunner.captured is None` (adapter never invoked), warning shown |
| Determinism | two independent runs → identical structural facts (spine, chapter names, non-linear flag, terms, image) |

## 6. Regression results

| Suite | Result |
|-------|--------|
| S12-07 (new) | 5 passed |
| S12-04 integration | 12 passed |
| S12-06 integration | 9 passed |
| S12-02 glossary integration | — (in 47 passed batch) |
| S12-03 glossary UX (UI) | — (in 47 passed batch) |
| S12-02/03/04/06/07 combined | 47 passed |
| reader_project (incl. `test_glossary_backend`, `test_recovery`) | 86 passed |
| S10-03 reader-first e2e | 6 passed |
| S10-03 recovery e2e | 12 passed |
| S11-04 spine ordering e2e + S11-07 non-linear e2e | 10 passed |
| S11-09/S11-10 TOC fallback | 12 passed |
| EPUB contract subset (S1/S2/S3/S5 + unit adapters) | 264 passed |

Broad regression classification: no S12-07-caused failures. Pre-existing residuals /
environment issues (legacy launcher collection, LCR/TIC fixtures, Windows filesystem
tests, shared Qt E2E fatal) are unchanged and untouched. `tests/reader_project/test_recovery.py`
re-ran the existing recovery contract unchanged.

## 7. S12-04 closure

S12-04 `EPUB Output` and `EPUB Fresh Read-back` move from BLOCKED to PASS. The other
S12-04 evidence (Glossary Backend, Glossary UI, TXT E2E, EPUB Option Binding) remains
PASS. S12-04 defect-evidence test was already flipped in S12-06; S12-07 re-runs it green.

## 8. Accounting

```text
Provider Execution        : 0
Network Execution         : 0
Real Translation          : 0
Production Files Modified : NO  (git diff -- core/ lts/ engine/ ui/ cli/ is empty)
Project schema            : unchanged
Runtime architecture      : unchanged
Provider / model          : unchanged
Recovery / hash           : unchanged
Security                  : unchanged
```

## 9. Files

```text
tests/integration/test_s12_07_glossary_epub_real_adapter_e2e.py        (new)
artifacts/NTPE_S12_07_GLOSSARY_EPUB_REAL_ADAPTER_E2E_REPORT.md          (this report)
```

Excluded / untouched: all `core/`, `lts/`, `engine/`, `ui/`, `cli/` production code;
S12-02/S12-03/S12-06 implementations; provider/model/runtime/schema/security;
pre-existing residuals (`memory/character_memory_lts.json` line-ending-only, the four
`tests/literary/outputs/*` with `PS-03/README.md` still deleted) and the untracked
S11-01/S11-02 artifacts. Temporary diagnostics lived in `D:\Temp\kilo` (outside the repo)
and were removed.

Diff hygiene: only the two S12-07 files are staged explicitly; `git add .`/`-A` not used.

## 10. Acceptance Matrix

| Gate | Result |
|------|--------|
| Baseline `83e34f0` | PASS |
| UI Import (real ProjectPage) | PASS |
| Project State persisted | PASS |
| Restart | PASS |
| EPUB Options canonical path/hash | PASS |
| Real Adapter | PASS |
| Offset Validation | PASS |
| Glossary Effect production-generated | PASS |
| Real Packaging | PASS |
| Persistence | PASS |
| Fresh Read-back | PASS |
| Terminology Output | PASS |
| Chapter Identity | PASS |
| Spine Order | PASS |
| Non-Linear | PASS |
| TOC | PASS |
| Resource Mapping | PASS |
| Replace | PASS |
| Detach | PASS |
| No Glossary | PASS |
| Corrupt | PASS |
| Recovery | PASS |
| Determinism | PASS |
| S12-06 / S12-04 / S12-03 / S11 / S10 | PASS |
| Provider / Network / Real Translation | 0 / 0 / 0 |
| Production Changes | NO |
| Legacy | untouched |
| Security | unchanged |
| Dirty State | preserved |
| Hygiene | PASS |

## 11. Decision

```text
S12_07_GLOSSARY_EPUB_REAL_ADAPTER_E2E_ACCEPTED
S12-04 = CLOSED
```

## 12. Commit

```text
test(glossary): verify EPUB real-adapter workflow
Push origin main · Tag: NO
```

*End of report.*
