# NTPE S11-08 — EPUB TOC Fallback Correctness Audit

Audit/design task. No production code, tests, schema, runtime, provider, model or TXT
changes. All findings are evidence-backed from repository source, existing tests and
temporary (non-committed, removed) diagnostics.

## 0. Baseline

```text
Baseline HEAD : c0938e4b396b3858a43954a4034b12f1afe3de72
Actual HEAD   : c0938e4b396b3858a43954a4034b12f1afe3de72
origin/main   : c0938e4b396b3858a43954a4034b12f1afe3de72
Branch        : main
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

## 1. TOC Problem Statement

When an EPUB chapter document provides no usable title (no `h1`/`h2`/`<title>`), NTPE is
supposed to fall back to the EPUB navigation/NCX label, and only then to a generated
`Chapter N`. The audit question is whether that fallback actually works and whether the
derived title is deterministic, stable and reader-safe, and whether it propagates to
chapter identity, preview, translation input, packaging and final navigation.

## 2. Standard Semantics (external reference, separated from NTPE product)

EPUB 3 Navigation Document (W3C EPUB 3.3 / EPUB 3 Navigation Document):

- A navigation document contains one or more `nav` elements; the table of contents is
  `nav` with `epub:type="toc"`.
- The `toc` nav contains an ordered list `ol`; each `li` contains an `a` (the label and
  the target) or a `span`, optionally followed by a nested `ol`.
- The nav reading order is defined by the navigation document, and is not required to be
  identical to the spine reading order.
- EPUB 2 uses the NCX `navMap/navPoint/navLabel/text` + `content/@src` structure.

Standard requirement: a conformant `toc` nav is `nav > ol > li > a(, ol)`; labels live on
the `a` (or `span`). Standard does not mandate any NTPE title precedence. Any "TOC label
wins / heading wins" rule is an NTPE product contract, not a standard requirement.

## 3. Repository Contract (authoritative sources found)

- Extraction precedence is documented in code:
  - `core/adapters/epub_extraction_boundary.py:1134` `_extract_title_from_doc`: `h1` >
    `h2` > document `<title>`.
  - `core/adapters/epub_extraction_boundary.py:1169` `_resolve_chapter_title_fallback`:
    "1. Mapped nav/NCX TOC title  2. Generated 'Chapter N'".
- Packaging contract: `core/epub_translation/runtime/epub_packager.py:474` builds nav
  "preserving original TOC structure" and prefers `translation_input.toc_entries` when
  present (line 478), else builds labels from chapter titles (line 482-493).
- Identity contract: `core/epub_translation/contract/models.py:71` `chapter_id` is
  `f"ch{spine_position:04d}"` — identity is spine position only, independent of title.
- Reader contract: `core/epub_translation/reader_chapter_map.py:269` prefers the input
  (extraction-derived) title, then a marker, then a generated `第N章`.

Documented/implemented fallback precedence:

```text
1. document <h1>
2. document <h2>
3. document <title>
4. nav/NCX TOC label mapped by base href     <-- documented, but non-functional (see §5)
5. generated "Chapter {chapter_index}"
```

Contract gap recorded (not invented semantics): the unit test name at
`tests/unit/adapters/test_epub_extraction_boundary.py:170`
(`test_chapter_title_precedence_nav_toc`) claims "nav TOC title wins", which contradicts
the code/docstring precedence (document headings first, TOC as fallback). The test cannot
distinguish the two because its fixture uses the same string for the `h1` and the nav
label. This precedence ambiguity is flagged for reconciliation; the repair below restores
the documented fallback tier without changing the heading-vs-TOC ordering.

## 4. Current Behavior Trace (per layer)

| Layer | Location | title source | fallback | chapter identity | href | spine_position | nav label |
|---|---|---|---|---|---|---|---|
| OPF metadata | `epub_extraction_boundary.py:392` | `dc:title` (book) | none | n/a | n/a | n/a | n/a |
| manifest | `:365` `_parse_manifest` | n/a | n/a | id | `href` | n/a | n/a |
| spine | `:377` `_parse_spine` | n/a | n/a | idref | (via manifest) | 1-based | n/a |
| nav (EPUB3) | `:421` `_parse_nav` | `a` text | none | mapped by href | link href | no | label |
| NCX | `:468` `_parse_ncx` | `navLabel/text` | none | mapped by href | `content/@src` | no | label |
| toc_map | `:509` `_build_toc_map` | first nav/NCX entry per base href | none | n/a | base href key | no | label stored |
| chapter extract | `:596` `_extract_chapter` | `_extract_title_from_doc` | None returned | n/a | manifest href | n/a | n/a |
| title select | `:204-207` in `extract` | extracted or fallback | `_resolve_chapter_title_fallback` | n/a | n/a | n/a | n/a |
| canonical intake | `canonical_book_intake_adapter.py:231` | passthrough | n/a | passthrough | passthrough | passthrough | passthrough |
| reader map | `reader_chapter_map.py:269` | input title | marker / `第N章` | `chapter_id` | n/a | n/a | n/a |
| translation input | `ui/.../controller.py:176`, `project_page.py:1125` | from chapter_map | n/a | `ch{spine:04d}` | source_href | spine_position | `toc_entries=()` |
| packaging nav | `epub_packager.py:468` | `input_chapter.title` | reader title / `第N章` | n/a | basename(source_href) | order | label |
| final EPUB | persisted `nav.xhtml` | chapter title | n/a | marker in body | xhtml basename | itemref order | label |
| read-back | `tests/e2e/test_s11_07...:271` | n/a | n/a | `[ZH:chNNNN]` | basename | itemref | not asserted |

Key production wiring fact: both production entry points set `toc_entries=()`:
- `ui/translation_launcher/controller.py:184`
- `ui/translation_studio/pages/project_page.py:1133`

Therefore the final `nav.xhtml` is always generated from chapter titles
(`epub_packager.py:482-493`), not from the original TOC. Navigation structure beyond one
entry per chapter (nested levels, fragments, sections) is not preserved in production.

## 5. Defects Found (reproducible)

### DEF-1 — EPUB 3 `nav > ol > li` TOC entries are never parsed

`_parse_nav` (`epub_extraction_boundary.py:444-445`) calls
`self._parse_nav_ol(nav, ...)`, but `_parse_nav_ol` (`:455-466`) traverses
`./xhtml:li` **directly under the element it receives**. For the standard structure
`nav > ol > li`, the direct children of `nav` are `ol`, so no `li` is found and the TOC is
always empty.

Evidence (isolated, lxml): for a conformant nav doc —
`//xhtml:nav[@epub:type='toc']` = 1; `nav/./xhtml:li` = 0; `nav/./xhtml:ol` = 1;
`ol/./xhtml:li` = 1. An end-to-end extraction of an EPUB3 fixture with a valid nav yields
`nav_toc_entries == 0`.

Effect: `nav_toc` is empty for every spec-conformant EPUB 3 nav. Only NCX (`_parse_ncx`,
which uses `.//ncx:navPoint`) works. Consequently `toc_map` is empty for EPUB 3, so
`toc_level` is always 0 for nav-based books as well (`:232`).

### DEF-2 — Fallback TOC lookup uses a field that does not exist

`_resolve_chapter_title_fallback` (`:1163-1179`) does:

```python
href = spine_item.get("href", "")      # spine items have NO "href" key
base_href = href.split("#")[0]         # always ""
if base_href in toc_map:               # always misses (unless a "" key exists)
    return toc_map[base_href]["title"]
return f"Chapter {chapter_index}"
```

Spine items are produced by `_parse_spine` (`:377-390`) with keys `idref`, `linear`,
`spine_position` only. The `href` lives in `manifest_items[item["idref"]]["href"]` and is
already resolved to `href`/`full_href` in `extract` (`:195-196`).

Evidence: `spine_item.get("href","")` → `''`; `_resolve_chapter_title_fallback({...}, {"ch1.xhtml": {...}}, 1)` → `'Chapter 1'`. An EPUB2 NCX fixture with no document title yields `nav_toc_entries == 1` but `chapter_map[0].title == 'Chapter 1'`; the NCX label (`NCX Chapter Title`) is silently dropped.

Effect: the documented TOC fallback tier is unreachable. Even when NCX parsing succeeds,
the chapter title never falls back to the TOC label.

### DEF-3 (adjacent, navigation helper) — `landmark_type` is never populated

`_parse_nav` parses landmarks into `nav_landmarks` (`:447-451`) and returns them
(`:152`), but `_build_toc_map` (`:509-531`) never receives or stores them, and its map
values are `{"title", "level"}` only. `:235` reads `toc_map.get(href, {}).get("landmark")`,
which is therefore always `None`. The existing test
`test_nav_landmarks_recorded` (`:1511`) asserts `landmark_type in ("chapter", None)`, which
always passes and hides the gap. Recorded as an adjacent observation; not part of the
title-fallback minimal repair.

### DEF-4 (edge) — empty/whitespace TOC labels can be stored and win

`_parse_nav_ol` (`:462`) and `_parse_ncx` (`:499`) can produce `""`; `_build_toc_map`
stores it and keeps the first key (`:523`), so a later valid entry for the same href is
ignored, and a naive repair could return a `""` reader-facing title. Evidence:
`_build_toc_map([{href:'a.xhtml',title:''},{href:'b.xhtml',title:'   '},{href:'a.xhtml#x',title:'Dup'}], ...)`
→ `{'a.xhtml': {'title': ''}, 'b.xhtml': {'title': '   '}}`. This is a guard requirement
for any repair (reader-facing title must be non-empty).

## 6. Input Variant Results

| Variant | Setup | Current result | Verdict |
|---|---|---|---|
| A Normal TOC | nav labels valid, doc `h1` present | `h1` title (TOC not consulted) | OK for title, but TOC path unproven |
| B Missing nav | no nav item | doc title else `Chapter N` | deterministic, non-empty |
| C Empty nav | `nav` present, empty `ol` | doc title else `Chapter N` | deterministic, non-empty |
| D Broken/unusable label | `a` with empty text | label silently dropped (DEF-4) | latent empty-title risk |
| E Missing chapter title metadata | no `h1`/`h2`/`<title>`, nav/NCX label present | `Chapter N` (DEF-1/DEF-2) | **defect** — label available but lost |
| F Duplicate/ambiguous titles | duplicate labels, distinct hrefs | identical labels, distinct `chapter_id` | deterministic, identity intact |

## 7. Fallback Requirements Assessment

- A Deterministic: PASS. Same fixture → same titles; `chapter_id`/order/href stable.
- B Stable vs identity/href/spine_position: PASS. Title is never used to derive identity;
  `chapter_id = ch{spine_position:04d}`.
- C Non-empty: PASS currently only because the TOC tier never fires. After any naive
  repair it can FAIL (DEF-4); repair must guard empty/whitespace labels.
- D Non-corrupting: PASS. No reordering, no identity change, resource mapping unaffected.

## 8. First Failure Layer / Root Cause

First failure layer: **A — Extraction fails to derive a usable title from an available
navigation source.** Downstream layers (B intake, C reader map, D packaging, E read-back)
faithfully carry whatever extraction produced and are not the loss point. F (fallback not
implemented) is the form of DEF-2 (tier present but mis-wired); G (test expectation) is a
secondary contributor, not the root cause.

Root cause (evidence-backed): two extraction-local logic bugs combine:
1. nav list traversal starts one level too high (DEF-1), and
2. the fallback resolver reads `href` from the spine item instead of the manifest item,
   so the TOC map lookup key is always empty (DEF-2).

## 9. Separation Checks (must hold)

- Chapter Identity: unchanged. `chapter_id` derives only from `spine_position`; fixing
  title fallback cannot renumber or re-identify chapters. `ch0001..ch000N` contract intact.
- Spine Ordering (S11-03 CLOSED): untouched. Repair touches only title derivation helpers.
- Non-Linear Semantics (S11-07 CLOSED): untouched. `item0 yes / item1 no / item2 yes /
  item3 no / item4 yes`, `is_linear`/`status` unaffected by title.
- Resource/href Mapping: unaffected. `ResourceRef` collection and `source_href` are
  independent of title; the packaging href is `basename(source_href)`.
- TOC order vs spine order: separate concepts; the repair does not impose TOC order on
  the spine and does not impose spine order on TOC parsing.

## 10. Reader / UI Impact

`ui/translation_studio/pages/project_page.py:129` renders each preview tab label as
`ch.get("title", "Chapter {index}")`, i.e. the extraction-derived chapter title. So the
DEF-1/DEF-2 loss is reader-visible: for chapters without in-document headings, preview
tabs (and the final EPUB nav labels) show a generic `Chapter N` instead of the book's real
TOC label. No other reader surface reconstructs navigation labels.

## 11. Final EPUB Navigation Impact

The packager rebuilds `nav.xhtml` from chapter titles because production always passes
`toc_entries=()` and because the extraction title is wrong, so:
- loss layer for TOC fallback = extraction (§8);
- loss layer for full original TOC structure (nesting/fragments) = navigation rebuild in
  packaging (`epub_packager.py:481-493`), which is existing product behavior and out of
  this task's repair scope.
Read-back parsers (`test_s11_07` and `test_s10_03`) do not assert nav labels, so the
defect is invisible to the closed E2E suites.

## 12. Existing Test Contract & Coverage Gap

Coverage that exists:
- `tests/contract/test_s5_epub_packaging.py:743` (S5-A-07) proves `toc_entries → nav
  labels/hrefs` preservation at the packaging layer (hand-built `TocEntry`s).
- `tests/unit/adapters/test_epub_extraction_boundary.py:170,178,215,251,286` exercise
  title precedence/fallback, and `:1306` exercises NCX parsing.
- S11-04/S11-07 E2E verify order/identity/non-linear/resource on fixtures whose chapter
  `h1 == <title> == expected`, and whose S11-07 fixture has no nav at all.

Coverage gap (the defect is not covered):
- No test asserts that a nav/NCX label is used when the document has no title. The two
  tests that name this behavior (`:170` "nav TOC title wins", `:1356` NCX titles) have
  fixtures where the document heading equals the TOC label, so they pass via
  `_extract_title_from_doc` without exercising the fallback. They are false positives.
- `nav_toc_entries` is never asserted for an EPUB3 nav extraction result.
- `landmark_type` is asserted with an always-true weak expression.
- No E2E asserts final `nav.xhtml` labels or reader preview tab labels.

## 13. Standards vs NTPE Requirement Separation

Standard requires `nav > ol > li > a` and defines label location; NTPE additionally
requires a deterministic title precedence and a non-empty reader-facing title fallback.
The repair fixes NTPE's own parser/fallback to consume standard-conformant nav; it does
not derive new UI behavior from the standard.

## 14. Minimal Repair Design (S11-09)

Decision gate: DEF reproducible (yes) + authoritative fallback source established
(nav/NCX TOC label, per repository docstrings/packager contract) + architecture can carry
it (yes, title already flows extraction → intake → translation input → reader map →
packager → final nav) + bounded (single file, three small changes).

Production file (only): `core/adapters/epub_extraction_boundary.py`

- R1 — `_parse_nav` (`:444-445`): descend into the `ol` child before parsing.

  ```python
  for nav in nav_root.xpath("//xhtml:nav[@epub:type='toc']", namespaces=ns):
      for ol in nav.xpath("./xhtml:ol", namespaces=ns):
          self._parse_nav_ol(ol, toc_entries, level=0, ns=ns)
  ```

  Expected: EPUB3 nav labels populate `nav_toc`; existing nested recursion keeps levels.
  Simulated result: `[{href:'ch1.xhtml',title:'TOC Chapter Title',level:0},
  {href:'ch2.xhtml',title:'Second',level:0},{href:'ch2.xhtml#s1',title:'Nested',level:1}]`.

- R2 — pass the manifest href into the fallback resolver. At the call site (`:205-207`)
  use the already-resolved `href` (manifest href, OPF-relative, consistent with the
  `toc_level` lookup at `:232`):

  ```python
  title = extracted_title or self._resolve_chapter_title_fallback(
      href, toc_map, chapter_index
  )
  ...
  def _resolve_chapter_title_fallback(self, href, toc_map, chapter_index):
      entry = toc_map.get((href or "").split("#")[0])
      if entry and (entry.get("title") or "").strip():
          return entry["title"].strip()
      return f"Chapter {chapter_index}"
  ```

  Update the legacy `_resolve_chapter_title` wrapper (`:1124-1132`) to the same parameter
  shape so it stays consistent. Simulated result: TOC/NCX label returned when present,
  `Chapter N` otherwise.

- R3 — in `_build_toc_map` (`:520-524`) skip entries whose stripped title is empty and
  keep the first non-empty title per base href, guaranteeing requirement C after repair.

Data source (authoritative fallback precedence, unchanged):
`document h1 > document h2 > document <title> > nav/NCX TOC label (base-href mapped) >
generated "Chapter {chapter_index}"`.

Explicitly excluded from the repair: `chapter_id`, `spine_position`, `source_href`,
manifest ids, resource mapping, original-TOC structural preservation, `landmark_type`
(DEF-3), and production `toc_entries=()` wiring. These are separate concerns.

## 15. Required Regression Tests (S11-09)

1. EPUB3 nav (`nav > ol > li`), chapter without `h1`/`h2`/`<title>` → title == nav label;
   `nav_toc_entries > 0`.
2. EPUB2 NCX, chapter without document title → title == NCX `navLabel`.
3. Empty/whitespace nav label, no document title → generated `Chapter N` (non-empty).
4. Missing nav and empty `ol`, no document title → `Chapter N`.
5. Correct `test_chapter_title_precedence_nav_toc` so `h1` and nav label differ and the
   asserted precedence reflects the reconciled contract (today it is a false positive).
6. Determinism: repeated extraction returns identical titles.
7. Separation: across all variants `chapter_id == ch{spine_position:04d}`, spine order and
   `is_linear`/status unchanged; resource mapping unchanged.

## 16. Required E2E Verification (S11-09, reader-first)

Full persisted path: extraction → canonical intake → translation input → reader chapter
map → `pack_epub_resource_aware` → persisted EPUB → fresh reopen. Fixture must keep the
closed `item0 yes / item1 no / item2 yes / item3 no / item4 yes` spine, one chapter with no
in-document heading, and a non-empty nav label. Assert:
- final `nav.xhtml` label for that chapter equals the TOC-derived title;
- body identity markers `ch0001..ch0005` and itemref order unchanged;
- `linear` attributes `[None,"no",None,"no",None]` preserved;
- referenced resource still present;
- repeated runs and restart/re-read are deterministic.

## 17. Security / Schema / Runtime

```text
Security : unchanged (no new input surface; same ZIP/nav parsing)
Schema   : unchanged (no Project or contract model change; reuses title/href/spine fields)
Runtime  : unchanged (no provider/model/TXT; title derivation is pre-runtime)
Provider : 0 changes
Legacy   : untouched
```

No STOP condition triggered: authoritative fallback source identified (STOP-A no);
no identity conflict (STOP-B no); no schema/two-pipeline/runtime change (STOP-C/D/E no);
standard and NTPE contract reconcile (STOP-F no); defect deterministically reproduced
(STOP-G no); it is a genuine parser/resolver defect, not merely a test-expectation bug
(STOP-H no).

## 18. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
Production Files Modified : NO
Tests Modified            : NO
```

## 19. Diff Hygiene

Only the audit artifact is added. `core/`, `lts/`, `engine/`, `ui/`, `cli/`, `tests/`
unchanged. Pre-existing dirty state preserved. Temporary diagnostics were created outside
the repository (`D:\Temp\kilo`) and deleted before completion.

## 20. Decision

```text
Decision: REPAIR
```

S11-08 PASS. Bounded, evidence-backed minimal repair defined for
`core/adapters/epub_extraction_boundary.py` (R1 nav traversal, R2 fallback href key, R3
empty-label guard). Next independent task: **S11-09 — EPUB TOC Fallback Minimal
Production Repair**, followed by its reader-first E2E verification.

Secondary, non-blocking items recorded for reconciliation (not part of this repair):
`landmark_type` never populated (DEF-3); production `toc_entries=()` discards original TOC
structure (existing behavior); heading-vs-TOC precedence wording inconsistency between the
unit test name and the code docstring.
