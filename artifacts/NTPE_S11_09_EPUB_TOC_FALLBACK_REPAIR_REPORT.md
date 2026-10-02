# NTPE S11-09 — EPUB TOC Fallback Minimal Production Repair Report

Minimal production repair in the existing EPUB extraction architecture, restoring the
nav/NCX TOC title fallback confirmed defective by S11-08. No new subsystem, schema,
runtime, provider, model or TXT change.

## 0. Baseline

```text
Baseline HEAD : c045da8e83c9a185f090692461c59f73202f060a
Branch        : main
origin/main   : c045da8 (as of task start)
```

Pre-existing dirty state preserved (never staged, never modified):

```text
 M memory/character_memory_lts.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md          (deleted state preserved)
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_S11_01_*.md
?? artifacts/NTPE_S11_02_*.md
```

## 1. Final Precedence Contract

One consistent, repository-backed hierarchy is now implemented, documented and tested:

```text
1. document <h1>
2. document <h2>
3. document <title>
4. nav / NCX TOC label (canonical source href, non-empty)
5. generated "Chapter {chapter_index}"
```

Why this is authoritative:

- `_extract_title_from_doc` (`core/adapters/epub_extraction_boundary.py`) already
  implements and documents `h1 > h2 > <title>`.
- `_resolve_chapter_title_fallback` is explicitly the fallback "when no title extracted
  from document", with the nav/NCX label first and the generated title last.
- The packager (`core/epub_translation/runtime/epub_packager.py:474-493`) documents its
  intent to preserve TOC structure and treats chapter titles as the nav-label source when
  `toc_entries` is absent (production always passes `toc_entries=()`), so a TOC-derived
  chapter title is the intended fallback label.

Contract ambiguity resolved: the unit test formerly named
`test_chapter_title_precedence_nav_toc` claimed "nav TOC title wins", which contradicts
the document-first implementation. Its fixture used `h1 == nav label`, so it could not
distinguish the two. The fixture now uses distinct strings and the test is renamed
`test_chapter_title_precedence_document_heading_over_nav_toc`, matching the unified
contract; a dedicated fallback test was added.

## 2. Repair Result

Production file: `core/adapters/epub_extraction_boundary.py` (only).

### R1 — EPUB 3 nav traversal — PASS

`_parse_nav` previously called `_parse_nav_ol(nav, ...)`, whose `./xhtml:li` traversal
missed the standard `nav > ol > li`. It now descends into the `ol` child(ren):

```python
for nav in nav_root.xpath("//xhtml:nav[@epub:type='toc']", namespaces=ns):
    for ol in nav.xpath("./xhtml:ol", namespaces=ns):
        self._parse_nav_ol(ol, toc_entries, level=0, ns=ns)
```

Standard `<nav epub:type="toc"><h2>…</h2><ol><li><a href="…">…</a></li></ol></nav>` and
nested `li > ol` both parse; the outer entry is not lost by nesting.

### R2 — Canonical href TOC lookup — PASS

`_resolve_chapter_title_fallback` no longer reads the non-existent `spine_item["href"]`.
It receives the already-resolved chapter `full_href` and looks up the TOC map with it.
The TOC keys are canonicalized by the new helper `_canonical_entry_href`, which mirrors
the existing `full_href` normalization (`posixpath.normpath(posixpath.join(doc_dir,
href))`) and strips fragments — no second, invented normalization scheme. The same
canonical key now drives the pre-existing `toc_level` / `landmark_type` lookups.

### R3 — Empty/whitespace label rejection — PASS

`_build_toc_map` trims labels, skips empty ones and keeps the first non-empty title per
base href; `_resolve_chapter_title_fallback` defensively re-checks. `None`, `""`, `"   "`
and `"\n\t"` can never become a reader-facing title.

## 3. Before / After Behavior

| Case | Before | After |
|---|---|---|
| EPUB3 nav label, no doc title | `nav_toc_entries=0`, title `Chapter N` | `nav_toc_entries>0`, title = nav label |
| EPUB2 NCX label, no doc title | NCX parsed but label dropped → `Chapter N` | title = NCX `navLabel` |
| doc `h1` + different nav label | `h1` (label ignored) | `h1` (doc heading outranks TOC) |
| whitespace nav label | `Chapter N` (lookup dead) | `Chapter N` (label explicitly rejected) |
| no nav/NCX | `Chapter N` | `Chapter N` (unchanged) |
| h3 only + nav label | h3 ignored, `Chapter N` | nav label (h3 is not a title source) |

## 4. Variant Results (temporary diagnostic, before tests written)

```text
A nav fallback        titles=['Chapter From Nav']                 nav_toc=1
B h1 wins             titles=['Document Heading']                 nav_toc=1
C ncx fallback        titles=['NCX Label One','NCX Label Two']    nav_toc=2
D whitespace label    titles=['Chapter 1']                        nav_toc=1
E no toc              titles=['Chapter 1']                        nav_toc=0
F fragment/x-href map titles=['Label For One','Label For Two']    nav_toc=3
G nested outer        titles=['Outer']                            nav_toc=2
H empty-first wins    titles=['Later Valid']                      nav_toc=2
subdirectory nav      titles=['Subdir Nav Label']                 nav_toc=1
```

EPUB3 nav: PASS. NCX: PASS. Missing TOC: PASS. Empty TOC: PASS. Invalid/whitespace
label: PASS. Fragment handling: PASS (base href stripped; `ch2.xhtml#s1` maps to the
`ch2` chapter without collapsing distinct documents). Subdirectory nav: PASS (relative
resolution against the navigation document directory).

## 5. Separation Checks

- Identity: unchanged. `chapter_id = f"ch{spine_position:04d}"`
  (`core/epub_translation/contract/models.py:71`); title does not participate.
- Spine ordering: unchanged. TOC order is never applied to the spine; chapter iteration
  remains ascending `spine_position`.
- Non-linear semantics: unchanged. `is_linear` / `status` untouched.
- Resource mapping: unchanged. `ResourceRef` collection and `source_href` are title-
  independent; test F asserts each label attaches to its own href.

## 6. Production Path Result

`tests/integration/test_s11_09_epub_toc_fallback_repair.py::test_production_path_toc_fallback_reaches_final_nav`
runs extraction → intake → `EpubTranslationInput` (`toc_entries=()`) → chunking →
deterministic injected runtime → `build_epub_reader_chapter_map_with_metadata` →
`pack_epub_resource_aware` → reads the packaged `nav.xhtml`. Result:

```text
labels == [("ch1.xhtml", "First From Nav"), ("ch2.xhtml", "Document H1 Two")]
```

The repaired fallback title reaches final navigation through the existing packager; the
higher-priority document `h1` still wins. Full persisted reader-first read-back is
deferred to S11-10.

## 7. Tests Added / Changed

- New: `tests/integration/test_s11_09_epub_toc_fallback_repair.py` — Tests A–F plus the
  production-path packaging assertion (7 tests).
- Changed (minimal): `tests/unit/adapters/test_epub_extraction_boundary.py`
  - `_create_minimal_epub` nav labels `"Nav One"/"Nav Two"` (distinct from the `h1`s).
  - renamed the false-positive precedence test and made it assert document-heading
    precedence with competing strings.
  - added `test_chapter_title_fallback_to_nav_toc_when_no_document_title`.

## 8. Regression Results

Targeted locks (all green):

```text
tests/unit/adapters/test_epub_extraction_boundary.py                       62 passed
S11-03 / S11-06 repair + S11-04 / S11-07 E2E                               17 passed
S10-03 reader-first + S10-03 recovery E2E                                  18 passed
tests/e2e (whole partition)                                                55 passed
all EPUB integration tests                                                 29 passed
tests/integration/test_s11_09_epub_toc_fallback_repair.py                   7 passed
```

Broad partitions:

```text
tests/unit + tests/contract : 3823 passed, 58 failed, 12 collection errors
tests/integration           : 1316 passed, 313 failed, 78 collection errors
```

No EPUB / S-series / TOC / spine / non-linear / reader test appears among the failures
(verified by grepping the failed list for `epub_extraction`, `s1..s5`, `toc`, `nav`,
`spine_ordering`, `non_linear`, `reader_first`, `s10_03`, `s11_`).

## 9. Broad Regression Classification

Pre-existing / environment (not caused by S11-09; unrelated modules or external state):

- Legacy `launcher_*` import-time `SystemExit` (known 81-test collection limitation).
- Legacy root-module `ModuleNotFoundError` (e.g. `ntpe_te_v40_stage401_*`,
  `ntpe_tic_batch2_*`) — modules outside the test tree.
- Fixture/artifact `FileNotFoundError` in LCR/TIC suites
  (`audits/legacy_capability_recovery/batch*`, `artifacts/tic_batch3`).
- Stale expectation tests unrelated to extraction, e.g.
  `tests/unit/adapters/test_production_submission_adapter.py` (`NTPE_RUNTIME_PIPELINE`
  env key), `tests/unit/translation_runtime/test_adapter.py` (`section_count 8 != 7`),
  `tests/unit/translation_release/reader_structure/test_epub_packager.py`
  (filesystem permission/invalid-path behavior).
- Global-worktree governance locks
  (`lcr_batch3_context_scene_memory_integration_test.py:101`,
  `lcr_batch4_chunk_cache_v2_integration_test.py:80`): they require the entire
  `git status` to fall inside their own batch allowlist. They are already violated by
  the pre-existing dirty state (literary residuals, untracked S11-01/02 artifacts) and by
  any unrelated task; they assert the presence of `core/adapters/epub_extraction_boundary.py`
  in the worktree change set, not its content correctness.

S11-09-caused failures: none found.

## 10. Provider / Network / Real Translation

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
```

Only a deterministic injected runtime is used, and only for the packaging-path check.

## 11. Modified / Excluded Files and Diff Hygiene

Modified / added:

```text
core/adapters/epub_extraction_boundary.py                 (R1/R2/R3)
tests/unit/adapters/test_epub_extraction_boundary.py      (precedence test fix + fallback test)
tests/integration/test_s11_09_epub_toc_fallback_repair.py (new)
artifacts/NTPE_S11_09_EPUB_TOC_FALLBACK_REPAIR_REPORT.md  (this report)
```

Excluded and untouched: `ui/`, `lts/`, `engine/`, `cli/`, Project schema, runtime,
provider, TXT, security, DEF-3 (`landmark_type`), original TOC hierarchy redesign,
pre-existing residuals, S11-01/02 untracked artifacts.

Hygiene: `.ntpe_test_sandbox/` generated by the broad run was removed; temporary
diagnostics lived outside the repository (`D:\Temp\kilo`) and were deleted. Final
`git status --short` contains only the intended S11-09 paths plus the preserved
pre-existing state.

## 12. S11-09 Acceptance

| Gate | Result |
|---|---|
| Baseline `c045da8` | PASS |
| R1 standard EPUB3 nav parsed | PASS |
| R2 canonical href lookup works | PASS |
| R3 empty/whitespace labels rejected | PASS |
| Precedence one consistent hierarchy | PASS (docstring/test/implementation aligned) |
| Nav fallback | PASS |
| NCX fallback | PASS |
| Final fallback `Chapter N` deterministic | PASS |
| Identity unchanged | PASS |
| Spine order unchanged | PASS |
| Non-linear unchanged | PASS |
| Resource mapping correct | PASS |
| Reader title corrected | PASS |
| Production path extraction → title → packaging | PASS |
| Existing regression no new S11 regressions | PASS |
| Provider 0 / Network 0 / Real Translation 0 | PASS |
| Security / Schema / Runtime unchanged | PASS |
| Legacy untouched | PASS |
| Dirty state preserved | PASS |
| Hygiene | PASS |

Explicit failure conditions FAIL-A..FAIL-L: none triggered.

## 13. Commit Boundary

Explicit staging only:

```text
core/adapters/epub_extraction_boundary.py
tests/integration/test_s11_09_epub_toc_fallback_repair.py
tests/unit/adapters/test_epub_extraction_boundary.py
artifacts/NTPE_S11_09_EPUB_TOC_FALLBACK_REPAIR_REPORT.md
```

Suggested commit message: `fix(epub): repair TOC title fallback`. Push `origin main`.
Tag: NO (`s11-complete` not created).

## 14. Next Boundary

Next independent task: **S11-10 — EPUB TOC Fallback Reader-First E2E Verification**
(source EPUB → production extraction → title fallback → translation pipeline → real
packaging → persisted final EPUB → fresh `nav.xhtml` read-back → reader-facing title
verification). S11-09 does not claim final-output E2E closure.
