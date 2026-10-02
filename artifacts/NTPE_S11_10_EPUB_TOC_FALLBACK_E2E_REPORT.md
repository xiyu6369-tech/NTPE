# NTPE S11-10 — EPUB TOC Fallback Reader-First E2E Verification Report

Verification-only closure of the S11-08 audit / S11-09 repair. No production change.

## 0. Baseline

```text
Baseline HEAD : 04d2e6ff742321d76810002d9536bdb1c2420178
Branch        : main
origin/main   : 04d2e6f (as of task start)
```

Pre-existing dirty state preserved (untouched, not staged):

```text
 M memory/character_memory_lts.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md          (deleted state preserved)
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_S11_01_*.md
?? artifacts/NTPE_S11_02_*.md
```

## 1. Verification Chain (real, not mocked)

```text
source EPUB (deterministic 5-item fixture, EPUB3 nav + NCX)
  -> production EpubExtractionBoundary.extract
  -> title derivation / TOC fallback (S11-09 R1/R2/R3)
  -> CanonicalBookIntakeAdapter.ingest_extracted
  -> EpubTranslationInput (toc_entries=(), production behaviour)
  -> chunk_epub_translation_input
  -> deterministic injected translation runtime (no provider/network)
  -> build_epub_reader_chapter_map_with_metadata
  -> real pack_epub_resource_aware -> persisted final EPUB
  -> fresh reopen (fresh zip handle / fresh ReaderProjectManager)
  -> parse final nav.xhtml -> title/href/identity verification
```

Extraction, title derivation, intake, chunking, packaging and read-back are not
mocked. Only the translation runtime is a deterministic injection.

## 2. Fixture Cases and Results

One deterministic fixture, spine `item0..item4` (`linear yes,no,yes,no,yes`), nav
entries deliberately listed out of spine order, NCX present, `img.png` referenced.

| Case | Item | Source title situation | Expected | Extraction | Final nav.xhtml |
|---|---|---|---|---|---|
| A nav fallback | item0 | no h1/h2/<title>; nav label | "First From Nav" | "First From Nav" | ("item0.xhtml","First From Nav") |
| C NCX fallback | item1 | no doc title; no nav entry; NCX label | "NCX Label One" | "NCX Label One" | ("item1.xhtml","NCX Label One") |
| B doc heading wins | item2 | `<h1>Document H1 Two</h1>`; nav label "Different TOC Label" | "Document H1 Two" | "Document H1 Two" | ("item2.xhtml","Document H1 Two") |
| D generated | item3 | no doc title; no nav/NCX entry | "Chapter 4" | "Chapter 4" | ("item3.xhtml","Chapter 4") |
| whitespace rejected | item4 | nav label `"   "`; no other source | "Chapter 5" | "Chapter 5" | ("item4.xhtml","Chapter 5") |

All expected values matched in extraction and, independently, in the persisted final
`nav.xhtml`. Case B truly uses competing strings (`h1 != nav label`), so the docstring/
implementation precedence `h1 > h2 > <title> > nav/NCX > "Chapter N"` is genuinely
exercised (no S11-08 false-positive fixture).

## 3. Final nav.xhtml (primary proof)

Actual persisted `nav.xhtml` link sequence read back by a fresh parser:

```text
("item0.xhtml", "First From Nav")
("item1.xhtml", "NCX Label One")
("item2.xhtml", "Document H1 Two")
("item3.xhtml", "Chapter 4")
("item4.xhtml", "Chapter 5")
```

- Source nav order was `item2, item0, item4` (different from spine); the production
  packager rebuilds navigation from chapters in spine order with `toc_entries=()`.
  Asserted property is therefore href→label correctness, not source-TOC order
  preservation. This existing rebuild behaviour was recorded as a known loss layer in
  S11-08 and is out of S11-09/S11-10 repair scope.
- Href → chapter identity: each `[ZH:chNNNN]` body marker matched its href
  (`item0..item4` ↔ `ch0001..ch0005`). No label attached to a wrong chapter (FAIL-D not hit).

## 4. Separation Locks

- Chapter identity: `ch0001..ch0005` = `ch{spine_position:04d}`; unchanged.
- Spine ordering (S11-03/S11-04): final spine `item0..item4`; unchanged.
- Non-linear semantics (S11-06/S11-07): final itemref linear values
  `[None, "no", None, "no", None]`; supplementary items neither removed nor moved.
- Resource mapping: `img.png` present in the persisted EPUB.
- TOC label change altered only display titles; identity/order/href untouched.

## 5. Persistence / Fresh Read-back / Restart / Determinism

- Persistence: test 4 creates a project via `ReaderProjectManager.create`, records
  `OutputRecord(artifact_kind="epub", available=True)` pointing at the pipeline output;
  the artifact exists on disk.
- Fresh read-back: tests 3/4/5 reopen the persisted EPUB with a fresh `zipfile` handle
  and parse `nav.xhtml`; test 4 additionally reopens through a brand-new
  `ReaderProjectManager(home=...)` (restart) and re-reads the same artifact.
- Restart: reloaded project's artifact path equals the original; nav labels, hrefs and
  identity markers identical after restart.
- Determinism: two independent runs produce identical `nav_links`, `chapter_entries`
  and linear semantics.

## 6. Test Placement (environmental constraint)

S11-10 verification is implemented as
`tests/integration/test_s11_10_epub_toc_fallback_reader_first.py` (5 tests, all pass),
not under `tests/e2e/`.

Reason (evidence-backed): the shared Qt e2e session has a pre-existing, flaky Windows
access violation in `test_s11_04_reader_first_ui_journey_persists_ordered_epub` — a
background QThread executing `translation_worker.run` → `TranslationRuntime.__init__` →
`resolve_api_key` (`core/ai_provider/credentials.py:49`) reading `os.environ`. Adding
*any* new e2e test module aborts the whole `tests/e2e` directory run:

```text
baseline tests/e2e (no new module)          : 55 passed  (4/4 runs)
full tests/e2e with a new e2e module        : abort (access violation) in S11-04
full tests/e2e with an unrelated probe file : crash in 1 of 2 runs
tests/e2e with tests appended to S11-07     : 60 passed (no new module)
```

The crash is in a pre-existing test and is timing/session sensitive, not caused by
S11-10 content. Placing S11-10 in the integration layer avoids importing Qt and keeps
`tests/e2e` green (55 passed). The full ProjectPage reader-first UI journey for this
same pipeline remains regression-locked by S10-03 and S11-07; the S11-10 module covers
the identical production chain plus a project-manager restart read-back.

## 7. Regression Results

```text
S11-03 spine ordering repair                       PASS
S11-04 spine ordering E2E                          PASS
S11-06 non-linear semantics repair                 PASS
S11-07 non-linear semantics E2E                    PASS
S11-09 TOC fallback repair (5 tests)               PASS
S11-10 reader-first verification (5 tests)         PASS
S10-03 reader-first E2E                            PASS
S10-03 recovery E2E                                PASS
combined regression + S11-10                       47 passed
tests/e2e directory                                55 passed
```

## 8. Broad Regression Classification

```text
tests/unit + tests/contract : 3823 passed, 58 failed, 3 skipped, 12 collection errors
tests/integration           : 1321 passed, 313 failed, 78 collection errors
tests/e2e                   : 55 passed
```

No EPUB / S-series / TOC / spine / non-linear / reader test appears among the failures
(grep of failed lists). Classified:

- S11-10-caused: none.
- Pre-existing / environment (identical to S11-09): legacy `launcher_*` import-time
  `SystemExit`; legacy root-module `ModuleNotFoundError`; LCR/TIC fixture
  `FileNotFoundError`; stale expectation tests (submission env key, prompt
  `section_count`, `reader_structure/epub_packager` filesystem behaviour);
  global-worktree governance allowlist locks.
- Environment (new): the flaky Windows access violation in the S11-04 UI test's
  QThread, documented in §6.

## 9. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
Production Files Modified : NO
Security / Schema / Runtime : unchanged
Legacy : untouched
```

## 10. Files and Diff Hygiene

Added:

```text
tests/integration/test_s11_10_epub_toc_fallback_reader_first.py
artifacts/NTPE_S11_10_EPUB_TOC_FALLBACK_E2E_REPORT.md
```

Production (`core/`, `lts/`, `engine/`, `ui/`, `cli/`): unchanged (`git diff -- core/`
empty). Pre-existing residuals and S11-01/02 artifacts preserved. `.ntpe_test_sandbox/`
generated by the broad run was removed; temporary diagnostics deleted.

## 11. S11-10 Acceptance

| Gate | Result |
|---|---|
| Baseline `04d2e6f` | PASS |
| Reader Path (real production chain) | PASS |
| Extraction correct fallback title | PASS |
| Intake title preserved | PASS |
| Chunking identity/order preserved | PASS |
| Real packager | PASS |
| Real persisted artifact | PASS |
| nav.xhtml actual read-back | PASS |
| Nav fallback survives | PASS |
| Document heading priority survives | PASS |
| NCX fallback survives | PASS |
| Empty label rejected | PASS |
| `Chapter N` deterministic | PASS |
| Href correct | PASS |
| Chapter identity unchanged | PASS |
| Spine order unchanged | PASS |
| Non-linear unchanged | PASS |
| Resource mapping correct | PASS |
| Persistence | PASS |
| Restart | PASS |
| Determinism | PASS |
| S11-09 / S11-07 / S10-03 regressions | PASS |
| Provider 0 / Network 0 / Real Translation 0 | PASS |
| Production change NO | PASS |
| Security / Schema / Runtime unchanged | PASS |
| Legacy untouched | PASS |
| Dirty state preserved | PASS |
| Hygiene | PASS |

Explicit failure conditions FAIL-A..FAIL-O: none triggered.

## 12. Commit Boundary

Explicit staging only:

```text
tests/integration/test_s11_10_epub_toc_fallback_reader_first.py
artifacts/NTPE_S11_10_EPUB_TOC_FALLBACK_E2E_REPORT.md
```

Suggested commit message: `test(epub): verify TOC fallback end to end`. Push
`origin main`. Tag: NO (`s11-complete` not created).

## 13. Closure

DEF-TOC now has a complete chain: Audit (S11-08) → Minimal Repair (S11-09) →
Regression → Reader-first persisted E2E verification (S11-10), with Spine Ordering and
Non-Linear Semantics staying CLOSED and resource mapping intact. The task did not
re-touch production. Return to S11 program-level audit rather than further EPUB
micro-repair.
