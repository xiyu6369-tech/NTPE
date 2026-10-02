# NTPE S11-03 — EPUB Spine Ordering Minimal Production Repair Report

Baseline HEAD: `1655b25dec83dd71707fbe46d09ee5fb73618c1e`
Actual HEAD (pre-commit): `1655b25dec83dd71707fbe46d09ee5fb73618c1e`
Branch: `main`
Tag: `s10-complete` (`s10-complete^{}` = `1655b25`)

Phase: S11-03 — minimal extraction repair + deterministic regression test.
Provider execution: 0. Network execution: 0. Real translation: 0.

---

## 1. Scope of Change

Production file changed (exactly one):

```
core/adapters/epub_extraction_boundary.py   (chapter emission ordering)
```

Test file added (exactly one):

```
tests/integration/test_s11_03_epub_spine_ordering_repair.py
```

Not modified (proven by diff boundary, §9): chunking, contract, reader chapter map,
runtime adapter, epub packager, UI, Project schema, TXT, security, runtime, provider,
model, legacy dead code.

---

## 2. Original Defect

`core/adapters/epub_extraction_boundary.py:178` (pre-repair):

```python
all_spine_items = linear_items + supplementary_items
```

`_parse_spine` already assigns the canonical key `spine_position` in spine itemref
document order (`:370-383`). Partitioning by `linear` and concatenating discards the
interleaving: an interspersed `linear="no"` item is emitted after all linear items,
producing a non-monotonic `spine_position` sequence and the wrong reading order.

Deterministic counterexample (spine `ch1(1,linear)`, `app(2,non-linear)`, `ch2(3,linear)`):

```
pre-repair:  [ch1, ch2, app]  spine_position [1, 3, 2]  chapter_id [ch0001, ch0003, ch0002]
canonical:   [ch1, app, ch2]  spine_position [1, 2, 3]  chapter_id [ch0001, ch0002, ch0003]
```

Note: manifest declaration order is irrelevant (order derives from spine itemref order);
the trigger is interspersed `linear="no"`. Established in S11-02.

---

## 3. Root Cause

```
Root cause:          A. Extraction ordering bug
First broken layer:  Extraction (epub_extraction_boundary.py:178)
Canonical owner:     Extraction
```

---

## 4. Exact Repair

`core/adapters/epub_extraction_boundary.py` (chapter loop):

```python
# Canonical reading order is the EPUB spine itemref order
# (`spine_position`). Partitioning by `linear` must not reorder
# interspersed linear="no" items; emit every spine item in
# ascending spine_position so ordering matches the canonical key.
all_spine_items = sorted(
    linear_items + supplementary_items,
    key=lambda it: it["spine_position"],
)
```

One ordering statement, at the earliest broken boundary. No downstream compensating sort.
No change to `chapter_id`, `spine_position` assignment, offsets, resources, security, or
manifest semantics.

### 4.1 Behavioural equivalence (why existing tests cannot regress)

`sorted(linear_items + supplementary_items, key=spine_position)` is **identical** to the
previous expression whenever the spine is all-linear (`supplementary == []`) or
all-supplementary (`linear == []`), because each partition preserves spine order.
Only interspersed mixed spines change — and S11-02 established that no existing test
fixture contained an interspersed non-linear spine item. Therefore every existing test
outcome is preserved.

---

## 5. Canonical Ordering Proof

Fixture (S11-03 regression test): spine
`item0(yes), item1(no), item2(yes), item3(no), item4(yes)`; manifest order
`item2, item0, item4, item1, item3`.

Asserted final order:

| field | value |
|---|---|
| `spine_position` | `[1, 2, 3, 4, 5]` |
| `index` | `[1, 2, 3, 4, 5]` |
| titles | `[item0, item1, item2, item3, item4]` |
| extracted-text marker order | `[item0, item1, item2, item3, item4]` |
| explicit negative assertion | `!= [1, 3, 5, 2, 4]` (pre-repair order) |
| offsets | contiguous; `[0, len(extracted_text)]` |

## 6. Non-linear Preservation Proof

```
is_linear == [True, False, True, False, True]
status    == ["linear", "supplementary", "linear", "supplementary", "linear"]
len(chapter_map) == 5   (nothing dropped)
```

## 7. Chapter Identity Proof

Extraction `ChapterBoundary` intentionally does not expose `chapter_id`; identity is
derived at the contract layer as `ch{spine_position:04d}`. After conversion to
`EpubChapterBoundary` (the same mapping the production UI uses), the test asserts:

```
chapter_id == ["ch0001", "ch0002", "ch0003", "ch0004", "ch0005"]
```

Identity is unchanged and remains spine-derived. (The S11-03 task text illustrated a
0-based `ch0000` example; the repository's canonical contract is 1-based
`_parse_spine` positions, which this repair preserves exactly.)

## 8. Manifest-Order Independence Proof

The fixture's manifest declaration order (`item2, item0, item4, item1, item3`) is asserted
to differ from the canonical order, yet extraction order follows the spine
(`item0..item4`). Manifest order is not the ordering source.

---

## 9. Regression Test

File: `tests/integration/test_s11_03_epub_spine_ordering_repair.py` (4 tests):

1. `test_interspersed_non_linear_items_preserve_canonical_spine_order` — A/B/C/offset/marker.
2. `test_canonical_order_independent_of_manifest_declaration_order` — D.
3. `test_extraction_is_deterministic` — E (repeat extraction identical output + hash).
4. `test_downstream_chunking_accepts_canonical_order_without_compensation` — contract
   identity (`ch0001..ch0005`) and chunk order == spine order with no compensating sort.

Deterministic, offline; tmp dirs only; no Qt/provider/network.

### Targeted result

```
tests/integration/test_s11_03_epub_spine_ordering_repair.py   4 passed
```

### EPUB-related regression result

```
tests/contract + tests/unit/adapters + tests/e2e + tests/reader_project
  + tests/integration/test_s10_02_epub_extraction_repair.py :  600 passed, 2 failed
tests/integration + tests/contract + tests/e2e + tests/reader_project
  -k "epub or spine or reader"                              :  402 passed, 0 failed
```

The 2 failures are unrelated to this repair (different module; see §10):
`tests/unit/adapters/test_production_submission_adapter.py` — a submission-adapter env-var
name and a stale `meta/llama-3.3-70b-instruct` expectation.

### Full regression result (honest status)

A single `python -m pytest -q` invocation is **not runnable** in this repository because
81 legacy `launcher_*`/`*_test.py` modules execute a subprocess at import and raise
`SystemExit`, aborting pytest collection (`INTERNALERROR`). There are also pre-existing
collection errors (`tests/unit/test_stage15_4_repetition_detection.py`,
`tests/unit/test_stage15_5_structure_integrity.py`, and a namespace-package
`ModuleNotFoundError` in `tests/contract/controlled_translation_runtime_integration/`).

Full suite was therefore executed in bounded partitions with the import-time-exit modules
excluded:

| Partition | Result |
|---|---|
| `tests/unit` | 3520 passed, 58 failed, 3 skipped, 2 collection errors |
| `tests/integration` | 1305 passed, 315 failed, 81 errors |
| EPUB-named subset (integration+contract+e2e+reader_project, `-k epub/spine/reader`) | 402 passed, 0 failed |
| Targeted S11-03 | 4 passed |

**All failures are pre-existing and unrelated to this repair.** They fall into
legacy frozen-artifact/inventory classes: `translation_engine_v710/v720_stage1xx`
freeze/canary/A-B validation, `lcr_batch*`, `tic_batch*`, `stage125x` canaries,
`stage15_*` quality, `stage17_2` scheduler, `public_api` frozen-module hash,
`launcher_product/test_gui_state`, and the previously-documented
`reader_structure/test_epub_packager.py` environment-sensitive `chmod` failures.

**Independence proof:** the production change is provably behaviour-identical for
all-linear and all-supplementary spines (§4.1), and no existing test fixture had an
interspersed non-linear spine (S11-02 §7). No failing test module imports
`core/adapters/epub_extraction_boundary.py` in an ordering-relevant way; the failing
classes are provider-canary/freeze/scheduler/quality subsystems with stale artifacts.

---

## 10. Known Pre-existing Failures (separated, not fixed)

- `reader_structure/test_epub_packager.py` permission/invalid-path — Windows/POSIX `chmod`.
- `lts_stage_01` TXT legacy expectations (root script `ntpe_translate_txt.py` absent).
- `test_production_submission_adapter.py` — env var `NTPE_RUNTIME_PIPELINE` and stale
  `llama-3.3-70b-instruct` default.
- Large `translation_engine_v7*_stage*`, `lcr_*`, `tic_*`, `stage125x`, `stage15_*`,
  `stage17_2`, `public_api` frozen-hash/inventory suites.

None were modified; none were "fixed" to make the suite green.

---

## 11. Excluded Pre-existing Dirty State (untouched / unstaged)

```
memory/character_memory_lts.json
tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
tests/literary/outputs/PS-03/README.md          (deleted, preserved)
tests/literary/outputs/Regression_History.json
tests/literary/outputs/Regression_History.md
```

Caveat (disclosed): the required regression run executed literary suites that may have
regenerated these residual outputs. They remain excluded and unstaged; no attempt was made
to restore or clean them.

### Test side-effects during regression (restored/removed)

The suite generated files; all were cleaned before commit:

- restored to HEAD bytes: `artifacts/knowledge_packages/v1/{manifest,package}.json`,
  `config/provider_environment_template.env`, `tests/literary/outputs/PS-03-smoke/*`
  (5 files; `git add --renormalize` cleared an `eol=lf` stat false-positive with
  worktree hash == HEAD hash for every file).
- removed (generated untracked): `.ntpe_test_sandbox/`, `release/`,
  `Compatibility_Report_RC_03.md`, `NTPE_1_1_LTS_STABLE_COMPLETE.md`,
  `Performance_Stabilization_Report_RC_03.md`, `RELEASE_NOTES_NTPE_1_1_LTS.md`,
  `Regression_Report_RC_03.md`, `Translation_Regression_Report_RC_03.md`.

---

## 12. Diff Boundary

```
core/adapters/epub_extraction_boundary.py                      | +9/-1  (intended)
tests/integration/test_s11_03_epub_spine_ordering_repair.py    | new     (intended)
artifacts/NTPE_S11_03_EPUB_SPINE_ORDERING_REPAIR_REPORT.md     | new     (this report)
```

No changes in runtime, provider, model, TXT, schema, packaging logic, security, UI, or
legacy code. No root scratch files. No second EPUB pipeline.

---

## 13. Acceptance Result

| Gate | Result |
|---|---|
| Baseline HEAD = 1655b25 | PASS |
| Repair at extraction owner | PASS |
| Only minimal spine ordering repair | PASS |
| Final order = spine_position ascending | PASS |
| Non-linear retained + `is_linear=False` | PASS |
| `chapter_id` unchanged and spine-derived | PASS |
| Manifest order does not control chapter order | PASS |
| Interspersed `linear="no"` fixture passes | PASS |
| Determinism | PASS |
| No downstream compensating sort | PASS |
| Runtime / Provider / Network / Real translation | unchanged / 0 / 0 / 0 |
| TXT / Project schema / Security unchanged | PASS |
| Legacy untouched | PASS |
| Existing contract assertions not weakened | PASS |
| Diff hygiene (unrelated changes removed) | PASS |
| Pre-existing dirty preserved and excluded | PASS |

**S11-03 Acceptance: PASS.**

---

## 14. Next Boundary

S11-04 — EPUB Spine Ordering E2E Verification owns the full
import → extraction → intake → chunking → translation entry → packaging → final EPUB
chapter order → persistence → reader-facing result verification.
No E2E is claimed here.

Commit: `fix(epub): preserve canonical spine ordering`.
Tag: none (S11 closure decides the tag boundary).
