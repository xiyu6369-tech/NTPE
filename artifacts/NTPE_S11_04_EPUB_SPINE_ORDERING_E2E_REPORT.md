# NTPE S11-04 — EPUB Spine Ordering Reader-First E2E Verification Report

Baseline HEAD: `cf77508f2ed4114625decfdbc39ceac69256b48a`
Actual HEAD (pre-commit): `cf77508f2ed4114625decfdbc39ceac69256b48a`
Branch: `main`
Tag: `s10-complete` (`s10-complete^{}` = `1655b25`)

Type: verification only. Production files modified: **NO**.
Provider execution: 0. Network execution: 0. Real translation: 0.

---

## 1. Fixture

Deterministic EPUB3, 5 chapters, manifest order deliberately differs from spine order.

```
Manifest order (declaration): item2, item0, item4, item1, item3, img
Spine order (document):       item0(yes), item1(no), item2(yes), item3(no), item4(yes)
Canonical spine_position:     1, 2, 3, 4, 5
Canonical chapter_id:         ch0001, ch0002, ch0003, ch0004, ch0005
Linear semantics:             T, F, T, F, T
Unique content markers:       CHAPTER_ITEM0 .. CHAPTER_ITEM4
Resource:                     img.png referenced by item0.xhtml
```

## 2. Verified Chain (real production path)

```
Source EPUB (interspersed linear="no")
  -> EpubExtractionBoundary.extract()
  -> CanonicalBookIntakeAdapter.ingest_extracted()
  -> EpubTranslationInput
  -> chunk_epub_translation_input()
  -> translate_epub_translation_input()  [deterministic injected runtime execution]
  -> build_epub_reader_chapter_map_with_metadata()
  -> pack_epub_resource_aware()          [real EPUB packaging]
  -> persisted final EPUB
  -> fresh reopen + OPF/spine parse
```

Ordering-critical layers are the real production code and were **not** mocked:
extraction, intake, input construction, chunking, packaging, final-EPUB parsing.
Only runtime *execution* (provider/model/network) and the OS opener are injected.

---

## 3. Results by Stage

| Stage | Observed | Verdict |
|---|---|---|
| Extraction order | `spine_position [1,2,3,4,5]`; titles `[item0..item4]`; `is_linear [T,F,T,F,T]`; explicit `!= [1,3,5,2,4]` | PASS |
| Intake | `submission_eligible=True`; positions/titles preserved | PASS |
| Translation input | `chapter_id [ch0001..ch0005]`; positions `[1..5]`; linear `[T,F,T,F,T]` | PASS |
| Chunking | first-occurrence chapter order `[ch0001..ch0005]`; per-chapter sequence `0..n-1` (no test-side sort) | PASS |
| Deterministic translation | chapter results in input order `ch0001..ch0005`; text carries `[ZH:chNNNN]` identity | PASS |
| Packaging | `pack_epub_resource_aware` success; final EPUB written | PASS |
| Final EPUB read-back | chapter hrefs `[item0.xhtml..item4.xhtml]`; markers `ch0001..ch0005` in order | PASS |
| Reader-facing order | chapter sequence `item0..item4` == canonical `spine_position 1..5` | PASS |
| Chapter identity | `item0->ch0001 ... item4->ch0005` at contract layer; final href→marker mapping correct | PASS |
| Resource mapping | `img.png` preserved and present in final EPUB; each spine item maps to correct content | PASS |
| Persistence / output | UI journey persists artifact (`artifact_kind="epub"`, `available=True`), reopenable | PASS |
| Determinism | two runs: identical `chapter_hrefs`, marker map, and spine signature | PASS |
| Supplementary retention | `item1` at chapter position 2, `item3` at position 4 (not moved to end) | PASS |

### Reader-first UI journey

`page._on_translate()` with `translate_epub_translation_input` patched to the deterministic
runtime; the real worker performed real packaging; the persisted artifact was reopened and
proved canonical order. A new `ProjectPage` reloaded the same persisted artifact with the
same order (lightweight restart, not a recovery test).

---

## 4. Finding DEF-1 — output EPUB does not emit `linear="no"` (separate, not fixed)

- Observation: in the packaged EPUB every `<itemref>` has no `linear` attribute (all default
  to linear). Supplementary source items lose their non-linear flag in the output.
- Evidence:
  - final spine parsed as `[('nav', None), ('ch1', None), ('ch2', None), ('ch3', None),
    ('ch4', None), ('ch5', None)]`;
  - `core/epub_translation/runtime/epub_packager.py:890-974` builds `book.spine` from item
    ids only; the file contains no reference to `linear`;
  - `tests/contract/test_s5*.py` never assert output linear preservation.
- Scope note: the **order** contract (the S11-03 defect and the S11-04 verification target)
  is satisfied — supplementary items are retained at their canonical positions, not moved to
  the end. Non-linear *attribute* propagation in the output EPUB is a distinct gap.
- Disposition: recorded as an independent workstream. **Not repaired in S11-04** (per S11-04
  §22 Case B: a new production defect must not be fixed here). The dedicated test
  `test_s11_04_final_epub_linear_attribute_observation` documents current behaviour so a
  future change is detected.

---

## 5. TOC

TOC fallback remains **DEFERRED** (S11-02 separate active gap) and was not repaired. The
final nav document is built from the chapter sequence in canonical order; ordering repair
did not break existing nav generation.

---

## 6. Test Results

### S11-04 targeted

```
tests/e2e/test_s11_04_epub_spine_ordering_e2e.py    6 passed
  - test_s11_04_extraction_preserves_interspersed_canonical_order
  - test_s11_04_intake_input_chunking_preserve_order_and_identity
  - test_s11_04_final_epub_spine_order_and_resource_mapping
  - test_s11_04_final_epub_linear_attribute_observation   (documents DEF-1)
  - test_s11_04_reader_first_ui_journey_persists_ordered_epub
  - test_s11_04_determinism_repeated_run_preserves_order_and_identity
```

### S10-03 regression + EPUB ordering surface

```
tests/e2e (incl. test_s10_03_epub_reader_first_e2e.py,
           test_s10_03_epub_recovery_e2e.py,
           test_s9_07_epub_reader_flow.py, test_s11_04_*)
 + tests/contract
 + tests/unit/adapters
 + tests/integration/test_s10_02_epub_extraction_repair.py
 + tests/integration/test_s11_03_epub_spine_ordering_repair.py
= 542 passed, 2 failed
```

The 2 failures are pre-existing and unrelated (different module; no ordering involvement):
`tests/unit/adapters/test_production_submission_adapter.py` — submission-adapter env var
`NTPE_RUNTIME_PIPELINE` and a stale `meta/llama-3.3-70b-instruct` default.

### Broad regression

Unchanged from S11-03: a single `python -m pytest -q` is blocked by 81 legacy `launcher_*`
modules that `raise SystemExit` at import (`INTERNALERROR`). Partitioned results:
`tests/unit` 3520 passed / 58 failed / 3 skipped / 2 collection errors; `tests/integration`
1305 passed / 315 failed / 81 errors. All failures are pre-existing legacy
frozen-artifact/canary/freeze/S15/lcr/tic/RC classes and the known
`reader_structure`/`lts_stage_01`/`production_submission_adapter` items. S11-04 added zero
failures.

---

## 7. Boundaries

| Item | Result |
|---|---|
| Production files modified | NO |
| Runtime / provider / model | unchanged |
| Project schema | unchanged (v1) |
| TXT pipeline | unchanged |
| EPUB security | unchanged |
| TOC repair | NO (DEFERRED) |
| Other S11 workstreams (Glossary/Character/Context/portability/legacy/QA/S7) | untouched |
| Provider / Network / Real translation | 0 / 0 / 0 |
| Existing S9/S10 assertions weakened | NO |

---

## 8. Diff Boundary

```
tests/e2e/test_s11_04_epub_spine_ordering_e2e.py          (new)
artifacts/NTPE_S11_04_EPUB_SPINE_ORDERING_E2E_REPORT.md   (new)
```

No `core/`, `lts/`, `engine/`, UI, CLI, schema, provider, runtime, TXT, or security change.

### Pre-existing dirty state (untouched, unstaged)

```
memory/character_memory_lts.json
tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
tests/literary/outputs/PS-03/README.md          (deleted, preserved)
tests/literary/outputs/Regression_History.json
tests/literary/outputs/Regression_History.md
```

---

## 9. Acceptance Gates

| Gate | Result |
|---|---|
| Baseline starts at cf77508 | PASS |
| Fixture interspersed `linear="no"` | PASS |
| Manifest deliberately differs from spine | PASS |
| Extraction canonical order preserved | PASS |
| Non-linear retained in spine sequence | PASS |
| Intake order preserved | PASS |
| Chunking order preserved | PASS |
| Translation deterministic and identity-preserving | PASS |
| Packaging final spine order preserved | PASS |
| Resource mapping correct | PASS |
| Read-back proves same order | PASS |
| Reader-facing canonical sequence preserved | PASS |
| Identity `ch0001..ch0005` unchanged | PASS |
| Determinism repeated run | PASS |
| Production modification | NONE |
| Runtime unchanged | PASS |
| Provider / Network / Real translation | 0 / 0 / 0 |
| TOC not repaired | PASS |
| Legacy untouched | PASS |
| Dirty state preserved | PASS |
| Hygiene | PASS |
| Output `linear="no"` propagation | NOT VERIFIED — DEF-1 recorded (separate workstream) |

**S11-04 Acceptance: PASS** for the EPUB spine ordering correctness gap fixed in S11-03.
DEF-1 (output non-linear attribute propagation) is recorded separately and is not claimed
as verified.

---

## 10. Conclusion

The S11-03 repair is verified end-to-end along the production path: an interspersed
non-linear source EPUB keeps canonical `spine_position` order and chapter identity through
extraction, intake, input, chunking, deterministic translation orchestration, real
packaging, persistence, and fresh read-back, with no downstream compensating sort. DEF-1 is
a distinct packaging gap to be scheduled independently.
