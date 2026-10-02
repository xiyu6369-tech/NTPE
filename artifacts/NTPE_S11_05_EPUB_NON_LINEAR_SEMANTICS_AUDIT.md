# NTPE S11-05 — EPUB Non-Linear Spine Semantics Audit & Minimal Repair Design

Baseline HEAD: `9fde445a138827626a56b17c13595fcd79b4c8b4`
Actual HEAD (pre-commit): `9fde445a138827626a56b17c13595fcd79b4c8b4`
Branch: `main`
`origin/main` = `9fde445`

Type: read-only audit + minimal repair **design**. Production = 0, Network = 0,
Real Translation = 0. Production files modified: **NO**. Tests modified: **NO**.

---

## 1. DEF-1 Statement (from S11-04)

> The source spine's `linear="no"` semantics are lost during EPUB packaging. Every
> chapter `<itemref>` in the final EPUB has no `linear` attribute, so EPUB semantics read
> them all as `linear="yes"`.

Reproduced independently in this audit (§5) with parser-level evidence.

---

## 2. External EPUB Semantic Reference

EPUB 3 Package Document (OPF) — `<spine>` is an ordered list of `<itemref>`; each
`<itemref>` may carry `linear`:

| Aspect | EPUB semantics |
|---|---|
| `<spine>` | ordered list of item references (reading order) |
| `linear="yes"` | part of the primary linear reading order |
| `linear="no"` | supplementary / auxiliary content |
| `linear` omitted | equivalent to `linear="yes"` |
| `linear="no"` | the item is **still in the spine**; it does not disappear |
| interleaving | allowed; non-linear items need not be moved to the end |

`linear` is a publication-semantics hint. Reading systems may present non-linear content
differently (or omit it from the default sequence), but the publication must still
*declare* it. NTPE's responsibility is faithful expression of the source publication's
declared semantics, not dictating a particular reader UI.

---

## 3. Canonical NTPE Semantics (repository contract)

Evidence that NTPE treats `linear` as first-class contract data:

| Evidence | Statement |
|---|---|
| `core/adapters/epub_extraction_boundary.py:164-183,226-229` | extraction parses OPF `linear` into `is_linear` + `status` (`"linear"`/`"supplementary"`) |
| `core/epub_translation/contract/models.py:56,60` | `EpubChapterBoundary.is_linear` ("True = reading order, False = supplementary"); `status` |
| `core/epub_translation/contract/models.py:157-164` | `linear_chapters` / `supplementary_chapters` properties (spine order) |
| `core/epub_translation/contract/validation.py:111-112` | `status` must be `"linear"` or `"supplementary"` |
| `tests/contract/test_s1_epub_contract.py:685-690` | `test_is_linear_preserved` — `is_linear` must be preserved |
| `tests/contract/test_s2_epub_chunking.py:417-421` | `test_supplementary_not_reordered` — supplementary stays in spine position |
| `tests/contract/test_s3_epub_runtime.py:471-476` | `test_supplementary_chapter_remains_in_spine_position` |
| `tests/contract/test_s4_epub_reader_chapter_map.py:1008-1013` | supplementary included in the reader map |
| `artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_DESIGN.md:18-19` | canonical contract: all spine items retained, non-linear marked |

Counter-evidence (ambiguity):

- No S5 packaging test asserts the **output** EPUB re-emits `linear="no"`.
- `EpubTranslationChunk`, `EpubChapterResult`, and `reader_structure.ChapterBoundary`
  do not carry a linear field (they do not need it for ordering/translation).
- The reader-facing UI does not currently expose a distinct supplementary status
  (it carries `is_linear` in book_info/preview but does not filter or label).

**Conclusion:** NTPE deliberately models `linear` as authoritative contract data and
preserves it up to the packaging boundary, but has no explicit output-fidelity contract
test for it. The gap is real (declared publication semantics change on packaging), and the
repository already carries the data needed to close it.

---

## 4. Full `linear` Data-Flow Trace

```
source EPUB OPF <spine><itemref linear="yes|no">
  -> EpubExtractionBoundary._parse_spine            is_linear / status / spine_position
  -> extraction ChapterBoundary (dataclass)          is_linear: bool, status: str
  -> CanonicalBookIntakeAdapter.ingest_extracted     passthrough (chapter_map)
  -> EpubTranslationInput.chapter_map                EpubChapterBoundary.is_linear / status
  -> chunk_epub_translation_input                    EpubTranslationChunk: NO linear field
  -> translate_epub_translation_input (result)       EpubChapterResult: NO linear field
  -> build_epub_reader_chapter_map_with_metadata     reader_structure.ChapterBoundary: NO linear field
  -> EpubPackagingInput                              has translation_input (chapter_map.is_linear)
  -> pack_epub_resource_aware internal book.spine    ids only; EpubItem.is_linear defaults True
  -> final EPUB <spine><itemref>                     NO linear attribute written
  -> read-back parser                                reads linear attr == None (correct)
```

### 4.1 Semantic Preservation Matrix

| Layer | Position | Identity | linear field | Status | Preserved? |
|---|---|---|---|---|---|
| Source EPUB | YES | href/idref | `linear="yes"\|"no"` | n/a | YES |
| Extraction | YES (`spine_position`) | href | `is_linear: bool` | `linear`/`supplementary` | YES |
| Intake | YES | href | `is_linear` (passthrough) | passthrough | YES |
| EpubTranslationInput | YES | `chapter_id` | `is_linear` | `status` | YES |
| Chunk (`EpubTranslationChunk`) | YES (`chapter_order`) | `chapter_id` | **absent** | absent | not carried (not needed) |
| Translation result (`EpubChapterResult`) | YES (`chapter_order`) | `chapter_id` | **absent** | absent | not carried |
| Reader chapter map (`ChapterBoundary`) | YES (`chapter_order`) | `chapter_id` | **absent** | absent | not carried (not needed) |
| Packaging input (`EpubPackagingInput`) | YES | `chapter_id` | available via `translation_input.chapter_map` | available | YES (available) |
| Packager internal `book.spine` | YES | `uid=ch{i}` | **not read**; `EpubItem.is_linear` defaults True | lost | **NO — LOSS** |
| Final EPUB | YES | `idref` | **absent** (`None`) | lost | **NO** |
| Read-back parser | YES | href | reads `None` | n/a | correct read of absent attr |

---

## 5. Independent Reproduction (parser-level)

Reusing the S11-04 interspersed fixture (`item0 yes, item1 no, item2 yes, item3 no,
item4 yes`; manifest order deliberately different), run through the real production path
(extraction → intake → input → chunking → deterministic runtime → packaging), the final
EPUB OPF parses as:

```
MANIFEST: ch1->item0.xhtml, ch2->item1.xhtml, ch3->item2.xhtml, ch4->item3.xhtml, ch5->item4.xhtml
SPINE:    [('nav', None), ('ch1', None), ('ch2', None), ('ch3', None), ('ch4', None), ('ch5', None)]
markers:  item0->ch0001, item1->ch0002, item2->ch0003, item3->ch0004, item4->ch0005
```

- Source `linear`: `yes,no,yes,no,yes`
- Final `linear`: all absent (⇒ `yes,yes,yes,yes,yes`)
- **Ordering and identity remain correct** (`item0..item4`, `ch0001..ch0005`).
- Read-back is not a false positive: the attribute is genuinely absent from the OPF.

---

## 6. First Semantic-Loss Layer

```
First loss layer:  Packager (epub_packager.py)
Category:          D — packaging input already carries sufficient data,
                   but the packager's internal spine representation drops it
Exact location:    core/epub_translation/runtime/epub_packager.py:890-936,973-974
Root cause:        `spine_items` is built from item ids only and the created
                   `EpubItem.is_linear` is never assigned (defaults True);
                   `book.spine = spine_items` therefore emits no `linear` attribute.
```

Not A/B/C: extraction/intake/input all preserve `is_linear`. Chunk/result/reader-map omit
the field but are not on the critical path for this value because `EpubPackagingInput`
mandatorily includes `translation_input`, whose `chapter_map[].is_linear` is available at
packaging time. Not E (serializer): ebooklib *does* support emitting `linear`; the packager
never sets it. Not F: the read-back parser correctly reports absence. Not G.

**Ordering is a separate contract** (S11-01..S11-04, CLOSED): order/identity are correct;
only the `linear` attribute is dropped.

---

## 7. Packaging API Capability (verified against installed library)

Installed: `ebooklib 0.20.0` (`D:\Python\Lib\site-packages\ebooklib\epub.py`).

- `EpubItem.__init__` sets `self.is_linear = True` (`:144`).
- `EpubWriter._write_opf_spine` (`:1037-1080`):
  - accepts `book.spine` entries that are `EpubHtml`/`EpubItem` objects or id strings;
  - for object entries uses `item.is_linear`; for string entries it looks up
    `book.get_item_with_id(id)` and uses `itm.is_linear`;
  - a `(item, "no")` tuple also forces non-linear (`:1050-1055`);
  - emits `linear="no"` only; omits the attribute for linear items (default yes).
- Round-trip loader: `book.spine = [(idref, linear)]` (`:1702`).

**Verdict:** the library fully supports the required semantics. No library replacement or
architecture change is needed. Repair can be one assignment at the packager chapter loop.

---

## 8. Product / Reader Relevance

- The reader-first product currently carries `is_linear` in the import/preview book_info
  (`ui/translation_studio/pages/home_page.py`) and includes supplementary chapters in
  translation and packaging; it does not filter or hide them.
- The product does not yet surface a distinct supplementary label; therefore the *reader
  UI* is not the primary justification.
- The authoritative justification is publication fidelity: the final EPUB currently
  declares every chapter as primary, which is a semantic change from the source and from
  NTPE's own contract model. Preserving the flag restores faithful semantics; consuming it
  in the UI (e.g., labelling supplementary chapters) is a separate, optional workstream.

---

## 9. Test Coverage Gap

- `tests/contract/test_s5*.py` construct chapters with `is_linear` but never assert the
  packaged EPUB's `linear` attribute.
- No S1–S5 test asserts output `linear` propagation.
- S11-04 added an *observation* test (`test_s11_04_final_epub_linear_attribute_observation`)
  that currently asserts all-`None`, documenting the gap.
- Nature of the gap: **missing production propagation AND missing output test** (not a
  test-only omission).

---

## 10. Minimal Repair Design (for S11-06, not implemented here)

### 10.1 Change

Single production file: `core/epub_translation/runtime/epub_packager.py`
(in the chapter loop, after `chapter_item` is created; around `:927-933`):

```python
chapter_item = epub.EpubItem(
    uid=f"ch{i}",
    file_name=output_href,
    media_type="application/xhtml+xml",
    content=xhtml_content.encode("utf-8"),
)
chapter_item.is_linear = bool(input_chapter.is_linear)   # NEW — preserve source linear
book.add_item(chapter_item)
```

`input_chapter` is already resolved at `:912` (`translation_input.chapter_map[...]`), so
the value is available with no model change. `book.spine` continues to hold id strings;
ebooklib's string path reads `get_item_with_id(id).is_linear`, so the attribute is emitted.

Alternative equivalent (explicit tuples): build `book.spine` entries as
`(chapter_item.id, "no" if not input_chapter.is_linear else "yes")`. The `is_linear`
assignment is smaller and leaves the spine data shape untouched, so it is preferred.

### 10.2 Exact API / field

- field: `EpubChapterBoundary.is_linear` (already present) → `EpubItem.is_linear`
  (existing library attribute).
- serializer: `ebooklib.epub.EpubWriter._write_opf_spine` emits `linear="no"`.

### 10.3 Test (S11-06)

- Replace the S11-04 observation assertion with a positive assertion that the final EPUB
  spine carries `linear="no"` exactly at the supplementary positions and no attribute at
  linear positions (i.e. `[None, "no", None, "no", None]` for the fixture), while order and
  identity remain `[item0..item4]` / `[ch0001..ch0005]`.
- Add a dedicated regression test (`tests/e2e/test_s11_06_epub_non_linear_semantics_e2e.py`)
  reusing the S11-04 harness.

### 10.4 Constraints respected

- No Project schema change; no runtime/provider/model/TXT change; no security change;
  no second pipeline; no renumbering of chapter identity; S11-03 ordering untouched.

---

## 11. Interaction Analysis

| Dimension | Interaction with the repair |
|---|---|
| Ordering (S11-03/04) | none — order is already correct and unaffected |
| Chapter identity | none — `chapter_id` unchanged; only the `linear` attribute is emitted |
| Resource mapping | none — resources/`href` unaffected |
| TOC | none — nav/TOC unaffected; TOC fallback stays DEFERRED |
| Security | none — ZIP/path/manifest/spine validation unchanged |
| Schema | none — `EpubPackagingInput` already carries `translation_input` |
| Runtime/provider/model | none |
| Legacy dead code | untouched |

---

## 12. Stop-Condition Check

| Stop condition | Status |
|---|---|
| STOP-A (cannot confirm NTPE requires preservation) | Not triggered as a hard stop — repository models `linear` as authoritative; recommendation below with explicit residual ambiguity |
| STOP-B (first-loss layer unknown) | Not triggered — Packager, category D |
| STOP-C (data model insufficient) | Not triggered — `is_linear` present at packaging boundary |
| STOP-D (second EPUB pipeline) | Not triggered |
| STOP-E (TXT/provider/model/security changes) | Not triggered |
| STOP-F (library cannot express semantics) | Not triggered — ebooklib 0.20.0 supports it |
| STOP-G (read-back false positive) | Not triggered — attribute genuinely absent |
| STOP-H (conflicts with authoritative contract) | Not triggered |

**No stop condition is triggered.**

---

## 13. Decision

```
Decision: REPAIR (minimal)
```

Rationale: The EPUB standard defines `linear` as declared publication semantics; NTPE's own
contract models `is_linear`/`status` as first-class and preserves them up to the packaging
boundary; the data is already available at that boundary; and the installed packaging
library can emit it. A one-line assignment restores fidelity with a bounded blast radius
and no schema/runtime/security change.

Residual ambiguity (disclosed): there is no explicit output-`linear` contract test today,
and the reader UI does not consume the flag. An owner who judges non-linear semantics
non-authoritative for NTPE output could choose KEEP AS-IS. The audit recommendation remains
REPAIR because dropping the attribute silently changes the declared publication semantics.

Next task (separate): **S11-06 — EPUB Non-Linear Spine Semantics Minimal Production Repair**
(followed by an E2E re-verification extending S11-04). S11-05 performs no implementation.

---

## 14. Diff Boundary

```
artifacts/NTPE_S11_05_EPUB_NON_LINEAR_SEMANTICS_AUDIT.md   (new)
```

No `core/ lts/ engine/ ui/ cli/ tests/` change. No commit of production/test code.

Pre-existing dirty state (untouched, unstaged):
`memory/character_memory_lts.json`,
`tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json`,
`tests/literary/outputs/PS-03/README.md` (deleted, preserved),
`tests/literary/outputs/Regression_History.json`,
`tests/literary/outputs/Regression_History.md`.
