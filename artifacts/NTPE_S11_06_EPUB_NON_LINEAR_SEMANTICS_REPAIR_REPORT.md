# NTPE S11-06 — EPUB Non-Linear Spine Semantics Minimal Production Repair Report

Baseline HEAD: `a8c083218c186f802234347e68df6b8660433e26`
Actual HEAD (pre-commit): `a8c083218c186f802234347e68df6b8660433e26`
Branch: `main`
Tag: `s10-complete` (unchanged)

Type: minimal production repair + regression test.
Provider execution: 0. Network execution: 0. Real translation: 0.

---

## 1. DEF-1 Root Cause (from S11-05)

At the packaging boundary the source `is_linear` value was already available via
`EpubPackagingInput.translation_input.chapter_map[].is_linear`, but the packager built
`book.spine` from item ids only and never set `EpubItem.is_linear` (ebooklib default
`True`). The serializer therefore emitted no `linear` attribute, turning a source
`yes,no,yes,no,yes` into an output `yes,yes,yes,yes,yes`.

First loss layer (unchanged): Packager — `core/epub_translation/runtime/epub_packager.py:890-936`.

---

## 2. Exact Production Change

Single file: `core/epub_translation/runtime/epub_packager.py` (chapter loop):

```python
chapter_item = epub.EpubItem(
    uid=f"ch{i}",
    file_name=output_href,
    media_type="application/xhtml+xml",
    content=xhtml_content.encode("utf-8"),
)
# Preserve the source spine's non-linear semantics. `is_linear` is
# already carried on translation_input.chapter_map; epublib emits
# linear="no" for items whose is_linear is False. Ordering/identity
# are unaffected.
chapter_item.is_linear = bool(input_chapter.is_linear)
book.add_item(chapter_item)
```

One assignment. No model/schema/runtime/provider/security/TXT change. `book.spine`
continues to hold id strings; ebooklib's string path reads
`book.get_item_with_id(id).is_linear` and emits `linear="no"` when False. No sort added;
no `linear="no"` item moved; no identity renumbered.

---

## 3. Semantics Before / After

| Value | Before | After |
|---|---|---|
| Source `linear` | `yes,no,yes,no,yes` | `yes,no,yes,no,yes` |
| Packaging input `is_linear` | `[T,F,T,F,T]` | `[T,F,T,F,T]` |
| Final EPUB chapter `<itemref linear>` | `None,None,None,None,None` (all default yes) | `None,"no",None,"no",None` |
| Final semantics | `yes,yes,yes,yes,yes` | `yes,no,yes,no,yes` |

`None` denotes the attribute is omitted (default `yes`); it is distinct from `"no"`.

---

## 4. Ordering / Identity / Resource Unchanged

| Dimension | Before | After |
|---|---|---|
| Final chapter order | `item0,item1,item2,item3,item4` | `item0,item1,item2,item3,item4` |
| `spine_position` | `[1,2,3,4,5]` | `[1,2,3,4,5]` |
| Chapter identity | `ch0001..ch0005` | `ch0001..ch0005` |
| Resource mapping | `img.png` preserved, hrefs correct | unchanged |
| Supplementary position | item1@2, item3@4 | item1@2, item3@4 |

No ordering code touched; S11-03 extraction repair untouched.

---

## 5. Regression Test

New: `tests/integration/test_s11_06_epub_non_linear_spine_semantics_repair.py` (3 tests).

Evidence chain is real, not in-memory: fixture → real extraction → intake →
`EpubTranslationInput` → chunking → deterministic injected runtime → real
`pack_epub_resource_aware` → **persisted EPUB** → fresh reopen → OPF `<spine>` parse.

Assertions:

- source/input `is_linear == [T,F,T,F,T]` and `status == [linear,supplementary,...]`;
- final spine chapter linear attributes `== [None,"no",None,"no",None]`, with an explicit
  check that positions 2 and 4 are `"no"` (not merely `None`);
- final chapter href order `== [item0.xhtml..item4.xhtml]`;
- final markers `== [ch0001..ch0005]`;
- resource `img.png` present.

The test does not mock `book.spine`, `EpubItem`, or the packager output.

### Updated S11-04 observation test

The S11-04 test `test_s11_04_final_epub_linear_attribute_observation` had deliberately
asserted the pre-repair defect (all attributes `None`). Per the S11-05 design it is renamed
to `test_s11_04_final_epub_linear_attribute_preserved` and now asserts the corrected
`[None, None, "no", None, "no", None]` (nav + chapters). This strengthens, not weakens, the
S11-04 suite; the S11-04 ordering assertions are unchanged.

### Targeted result

```
tests/integration/test_s11_06_epub_non_linear_spine_semantics_repair.py
tests/integration/test_s11_03_epub_spine_ordering_repair.py
tests/e2e/test_s11_04_epub_spine_ordering_e2e.py
tests/e2e/test_s10_03_epub_reader_first_e2e.py
tests/e2e/test_s10_03_epub_recovery_e2e.py
tests/contract
= 369 passed
```

### Broad regression

Partitions (81 import-time-`SystemExit` legacy modules excluded; single `pytest -q`
remains non-runnable as established in S11-03):

| Partition | Result | vs S11-03/04 baseline |
|---|---|---|
| `tests/unit` | 3520 passed, 58 failed, 3 skipped, 2 errors | identical |
| `tests/integration` | 1308 passed, 315 failed, 81 errors | +3 passed (the new S11-06 tests); failures/errors identical |

All failures remain pre-existing legacy classes
(`translation_engine_v7*_stage*`, `lcr_*`, `tic_*`, `stage125x`, `stage15_*`, `stage17_2`,
`public_api` frozen-hash, `launcher_product/test_gui_state`, `reader_structure` chmod,
`lts_stage_01`, `production_submission_adapter`). S11-06 introduced zero new failures.

---

## 6. Side-Effect Control

The broad run generated `.ntpe_test_sandbox/`, which was removed. No root reports,
`release/`, or regenerated tracked files remained. The five pre-existing residuals were not
staged or modified by this task.

---

## 7. Diff Boundary

```
core/epub_translation/runtime/epub_packager.py                          (+5/-0)
tests/integration/test_s11_06_epub_non_linear_spine_semantics_repair.py (new)
tests/e2e/test_s11_04_epub_spine_ordering_e2e.py                        (observation → preserved assertion)
artifacts/NTPE_S11_06_EPUB_NON_LINEAR_SEMANTICS_REPAIR_REPORT.md        (new)
```

No `core/adapters/`, `lts/`, `engine/`, `ui/`, `cli/`, schema, runtime, provider, TXT, or
security change. No second EPUB pipeline. No TOC fallback repair.

Pre-existing dirty state (untouched, unstaged):
`memory/character_memory_lts.json`,
`tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json`,
`tests/literary/outputs/PS-03/README.md` (deleted, preserved),
`tests/literary/outputs/Regression_History.json`,
`tests/literary/outputs/Regression_History.md`.

---

## 8. Acceptance Matrix

| Gate | Result |
|---|---|
| Baseline `a8c0832` | PASS |
| First loss remains packager | PASS |
| Repair owner `epub_packager.py` | PASS |
| Source semantics `T,F,T,F,T` | PASS |
| Final semantics `yes,no,yes,no,yes` | PASS |
| Non-linear explicit `linear="no"` | PASS |
| Ordering `item0..item4` unchanged | PASS |
| Spine position `1..5` unchanged | PASS |
| Chapter identity `ch0001..ch0005` | PASS |
| Resource mapping unchanged | PASS |
| Final EPUB real artifact | PASS |
| Read-back fresh parser | PASS |
| S11-03 regression | PASS |
| S11-04 regression | PASS |
| S10-03 regression | PASS |
| Provider / Network / Real translation | 0 / 0 / 0 |
| Security / Schema / Runtime | unchanged |
| Legacy untouched | PASS |
| Dirty state preserved | PASS |
| Hygiene | PASS |

**S11-06 Acceptance: PASS.**

---

## 9. Boundary After S11-06

Do not claim the reader-first semantics E2E is closed here. The next independent
verification is **S11-07 — EPUB Non-Linear Spine Semantics Reader-First E2E
Re-verification**, which must extend/rerun the S11-04 harness through
source → extraction → intake → chunking → deterministic translation → packaging →
persisted final EPUB → fresh read-back and confirm `T,F,T,F,T` end-to-end plus the final
`None/no/None/no/None` representation. S11-06 implements only the production propagation.

Commit: `fix(epub): preserve non-linear spine semantics`. Tag: none.
