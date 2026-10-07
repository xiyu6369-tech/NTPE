# NTPE S12-05 — EPUB Chunk Offset Contract Reconciliation Audit

Audit only. No production file modified, no test modified.

## 0. Baseline

| Metric | Value |
|--------|-------|
| Baseline HEAD | `e4ad3508a2e6efc18565a90a5b908e8efaa47d3b` |
| Actual HEAD | `e4ad3508a2e6efc18565a90a5b908e8efaa47d3b` |
| origin/main | `e4ad3508a2e6efc18565a90a5b908e8efaa47d3b` |
| Branch | `main` |

Baseline verified with `git status --short`, `git branch --show-current`,
`git rev-parse HEAD`, `git rev-parse origin/main`. No reset/clean/stash/restore was run.
Pre-existing dirty state preserved (see §14).

## 1. Result Summary

```text
Independent reproduction (no glossary) : PASS (deterministic, offline)
First failure layer                     : validate_epub_translation_chunk
Root cause classification               : B — validator compares incompatible coordinate spaces
Canonical offset contract               : DECIDED (see §11)
Decision                                : REPAIR (validator, single owner; see DESIGN)
Production Files Modified               : NO
Tests Modified                          : NO
Provider / Network / Real Translation   : 0 / 0 / 0
```

The reported S12-04 defect is confirmed and is a **contract mismatch between two
layers**, not a chunker bug and not a glossary bug. The chunker is compliant with the
authoritative contract; the validator is the non-compliant layer.

## 2. Reproduction

Deterministic, offline reproduction with **no provider, no network, no glossary, no
Qt session, no injected adapter**:

```text
source EPUB (3 chapters, each with an extraction marker prefix)
-> EpubExtractionBoundary().extract()
   ch1: start=0   end=890  body=[29,889)   marker_len=29   (body slice == pure body)
   ch2: start=890 end=1782 body=[920,1781) marker_len=30
   ch3: start=1782 end=2676 body=[1813,2675) marker_len=31
-> validate_epub_translation_input()                       PASS
-> chunk_epub_translation_input()
   ch0001:chunk0000: extracted=[29,889) body=[0,860)   body_range=860 == extracted_range=860
   ch0002:chunk0000: extracted=[920,1781) body=[0,861) body_range=861 == extracted_range=861
   ch0003:chunk0000: extracted=[1813,2675) body=[0,862) body_range=862 == extracted_range=862
-> validate_epub_translation_chunk(ch0001:chunk0000)
   ContractValidationError: chunk body_start_offset (0) < extracted_start_offset (29)
-> validate_chunk_ownership(...)  -> same error
```

Mapping proof inside the reproduction:

```text
chapter.body_start_offset      = 29
chunk0.extracted_start_offset  = 29
chunk0.body_start_offset       = 0
extracted_text[extracted_start:extracted_end] == chunk.source_text   -> True
```

The `extracted_*_offset` values are **correct and self-consistent** with
`source_text`. The `body_*_offset` values are a correct value in a **different
coordinate space**.

### 2.1 Marker prefix identity

The `29` is the synthetic extraction chapter marker:

```text
"=== CHAPTER 1: <title> ===\n"  =  20 + len(title)  characters
```

It is **not** a heading, metadata prefix, wrapper, or normalized-source artifact. It is
produced at `core/adapters/epub_extraction_boundary.py:226` and prepended to every
chapter block. Confirmed against the actual fixtures:

- `tests/integration/test_s10_02_epub_extraction_repair.py:194` asserts
  `text[ch.start_offset:ch.start_offset+len(marker)] == marker`.
- `tests/e2e/test_s10_03_epub_reader_first_e2e.py:283-285` asserts
  `body_start == ch.start_offset + len(marker)` and `body_end == ch.end_offset - 1`.

### 2.2 Negative reproduction (Case B — compatible offsets)

When the marker length is 0 (so chapter `body_*` coincides with chapter
`start/end`), the chunker still emits `body_start_offset = 0` and
`extracted_start_offset = 0`; the two coincide and **validation passes**.

```text
marker_len == 0  =>  validation_failures = 0
marker_len  > 0  =>  every chapter's first chunk fails (body_start=0 < extracted_start=marker_len)
```

Therefore the defect is triggered precisely by the marker-prefix interaction, and it
is a **coordinate-space mismatch**, not a "case B also fails" broader defect.

### 2.3 Glossary independence

```text
glossary attached  : same ContractValidationError (S12-04 evidence test)
glossary detached  : same ContractValidationError (this reproduction, no glossary at all)
```

Structural proof: the adapter validates chunks at
`core/epub_translation/runtime/adapter.py:274`, **before** the glossary loader runs at
`adapter.py:281`. `chunking.py` and `validation.py` do not import any glossary module
(`tests/contract/test_s2_epub_chunking.py::TestTXTRegression` also asserts chunking
imports no runtime). `DEF-OFFSET != Glossary defect`.

## 3. Field-by-field offset semantics

Legend — inclusive/exclusive: all ranges are half-open `[start, end)`, 0-based code
points, `length = end - start`.

| Field | Model | Meaning | Coordinate space | Origin | Consumer | Unit |
|-------|-------|---------|------------------|--------|----------|------|
| `start_offset` / `end_offset` | `ChapterBoundary` (extraction), `EpubChapterBoundary` (contract) | marker-inclusive chapter block `marker + body + "\n"` | **Space C** absolute in `extracted_text` | `epub_extraction_boundary.py:229-230` | chunker bounds; ownership validation | code points |
| `body_start_offset` / `body_end_offset` | `EpubChapterBoundary` (contract) / `ChapterBoundary` (extraction) | pure chapter body (marker-free, trailing-newline-free) | **Space C** absolute in `extracted_text` | `epub_extraction_boundary.py:237-238` | chunker slices `extracted_text[body_start:body_end]`; validated range | code points |
| `extracted_start_offset` / `extracted_end_offset` | `EpubTranslationChunk` | chunk span in `extracted_text` | **Space C** absolute in `extracted_text` | `chunking.py:182-183,194-195` | ownership validation only (not used for translation/output) | code points |
| `body_start_offset` / `body_end_offset` | `EpubTranslationChunk` | chunk span **within its chapter body** (0 = chapter body start) | **Space B** chapter-body-relative | `chunking.py:177,196-197` | model invariant; validator (currently misinterpreted) | code points |
| `source_start_offset` / `source_end_offset` | TIC alignment units (`core/translation_intelligence_corpus/*`) | unrelated corpus/alignment fields | not EPUB | alignment layer | TIC only | code points |

**Naming hazard (documentation debt, not the defect):** the identifier
`body_start_offset` carries **two different meanings** on two different models —
absolute-in-`extracted_text` on `EpubChapterBoundary`, but chapter-body-relative on
`EpubTranslationChunk`. The chunker is the only bridge between them.

### 3.1 Inclusivity / exclusivity

Consistent across extraction and chunk layers: `[start, end)`, `length = end - start`.
Verified in reproduction (`body_range == extracted_range`, `body_end == end_offset - 1`).
The only layer that breaks the convention is the validator, which treats body-relative
offsets as if they were absolute (see §7).

### 3.2 Coordinate spaces named from repository evidence

| Space | Definition | Used by |
|-------|------------|---------|
| A | raw EPUB XHTML resource bytes (`0..len(raw)`) | not used by any of these offsets |
| B | extracted chapter document offset (chapter-body-relative) | `EpubTranslationChunk.body_*` |
| C | marker-inclusive extracted offset in `extracted_text` | `ChapterBoundary.start/end`, `EpubChapterBoundary.start/end/body_*`, `EpubTranslationChunk.extracted_*` |
| D | normalized/transformed text | not used by chunk offsets (see §9.2) |
| E | assembled translated output | `ReaderChapterMap` chapter positions (`reader_chapter_map.py:45-109`) |

No new space is invented; all names map to existing repository semantics.

## 4. Extraction / ChapterBoundary audit

`core/adapters/epub_extraction_boundary.py:187-259` builds one `extracted_text` by
concatenating, per spine item:

```text
full_chapter_text = marker + chapter_text + "\n"
start_offset      = current_offset
end_offset        = current_offset + len(full_chapter_text)
body_start_offset = start_offset + len(marker)
body_end_offset   = body_start_offset + len(chapter_text)
```

The inline comment at lines 232-236 explicitly states that all three quantities share
**one coordinate space** (absolute in `extracted_text`). Extraction is internally
consistent; S10-02 repair semantics are confirmed correct by
`test_s10_02_epub_extraction_repair.py` and `test_e2e_real_extraction_offsets_identity`.
Extraction is **not** the defect layer.

The contract `EpubChapterBoundary` copies these fields verbatim through
`CanonicalBookIntakeAdapter` (`ui/translation_launcher/controller.py:130-147`,
`ui/translation_studio/pages/project_page.py:1270-1279`). Its docstring
(`models.py:33-48`) correctly documents the absolute space.

## 5. Chunking audit

`core/epub_translation/chunking.py`:

- `_ParagraphChunkEngine.split(text, 0)` returns offsets relative to chapter body start
  (`chunking.py:51-56,176-177`).
- `_chunk_chapter_body` converts to absolute for the `extracted_*_offset` fields
  (`chunking.py:181-183`) and stores the **relative** values in `body_*_offset`
  (`chunking.py:194-197`).
- `chunk_epub_translation_input` validates each chapter boundary, slices
  `extracted_text[body_start:body_end]`, and re-checks that every chunk's extracted span
  lies within the chapter body (`chunking.py:236-301`).

The chunker's `body_start_offset = 0` is an **intentional chapter-body-relative**
offset, not an accidental unnormalized one. Evidence:

1. Explicit conversion/assignment of the relative variables (`chunking.py:182-197`).
2. `EpubTranslationChunk.__post_init__` (`models.py:197-215`) admits a different origin
   when `body_range == extracted_range`, with the comment "cross-coordinate
   'violations' are valid coordinate system differences".
3. `tests/contract/test_s2_epub_chunking.py::TestOffsetIntegrity::test_body_offsets_remain_body_offsets`
   asserts chunk body offsets are body-relative.
4. Prior accepted decision `artifacts/NTPE_S5_VALIDATION_DEFECT_REPAIR_01_REPORT.md` §2.3:
   "`body_*_offset` are relative to chapter body (0-based); `extracted_*_offset` are
   absolute in `extracted_text` (marker-inclusive)".

Chunk text / offset consistency: `extracted_text[extracted_start:extracted_end] ==
chunk.source_text` holds (proved in §2). `body_start_offset`/`body_end_offset` map into
the chapter body slice, i.e. `chapter_body[body_start:body_end] == source_text`. Both are
coherent within their own spaces. **Chunker is compliant.**

## 6. Model contract audit

`EpubTranslationChunk.__post_init__` (`models.py:189-215`):

```text
extracted_end >= extracted_start
body_end      >= body_start
body_range = body_end - body_start ; extracted_range = extracted_end - extracted_start
if body_range == 0: return                      (empty body allowed anywhere)
if body_range != extracted_range:               (only then compare positions)
    body_start < extracted_start -> "body_start_offset must be >= extracted_start_offset"
    body_end   > extracted_end   -> "body_end_offset must be <= extracted_end_offset"
    else                         -> "body range must equal extracted range"
```

The model enforces the **correct canonical invariant** (`body_range == extracted_range`
for non-empty chunks) and deliberately allows a different origin. The containment error
strings exist only as diagnostics for the case where ranges already differ. The model is
**compliant** with the canonical contract. Its field comments (`models.py:184-185`,
"In extracted_text, body-relative …") are internally contradictory and are
documentation debt, but the executed invariant is coherent.

## 7. Validator audit

`core/epub_translation/contract/validation.py:176-203` (`validate_epub_translation_chunk`)
enforces:

```text
extracted_end_offset >= extracted_start_offset
body_end_offset      >= body_start_offset
body_start_offset    >= extracted_start_offset     <-- cross-space comparison
body_end_offset      <= extracted_end_offset       <-- cross-space comparison
```

The last two comparisons assume `body_*` and `extracted_*` are in the **same** coordinate
space. Under the canonical contract they are not (`body_*` = Space B, `extracted_*` =
Space C), so these comparisons are **invalid** and reject every compliant chunk that has a
non-zero marker prefix. This is the **first (and only) failing layer**.

The comparison is not merely "too strict" — it is checking the wrong relation. The
correct chunk-local relation is the same-space invariant `body_range == extracted_range`
(the model's invariant), which the validator does **not** currently check. Separately,
`validate_chunk_ownership` (`validation.py:374-384`) checks `extracted_*` against the
chapter's **marker-inclusive** `start/end`, which is valid (same space) though looser than
the chapter body range.

## 8. Adapter audit

`core/epub_translation/runtime/adapter.py:247-274`:

- `translate_epub_translation_input` calls `validate_chunk_ownership(translation_input,
  chunks)` at line 274 as its first substantive action.
- The adapter **never reinterprets offsets**: it consumes `chunk.source_text`,
  `chunk.chunk_id`, `chunk.chapter_id`, `chunk.chapter_order`, `chunk.chunk_sequence`,
  `chunk.source_href`, `chunk.fragment` only.
- Offsets are not passed to the runtime, not persisted, not used for assembly.

The adapter does not "expect" an offset contract of its own; it inherits the validator's.
It fails only because it calls the non-compliant validator — exactly the S12-04 evidence.

## 9. Downstream contract audit

### 9.1 Translation runner / packaging / output

`ReaderChapterMap` / `epub_packager` compute chapter positions from the **assembled
translated text** (`reader_chapter_map.py:45-109`), a new Space E, and never read chunk
offsets. So packaging/output do not need a second offset interpretation; after the repair
they require **no change**.

### 9.2 Latent hygiene note (not the defect)

Extraction computes offsets on the pre-join per-chapter text and then normalizes the
whole `extracted_text` (`\r\n`/`\r` -> `\n`) at `epub_extraction_boundary.py:262`. Per
chapter, `_normalize_text` (`:1107-1113`) already performs the same newline normalization,
so the concatenation contains no `\r` and the post-pass is a no-op. Recorded as latent
hygiene only; it does not contribute to this defect.

### 9.3 Hash / integrity

- `extracted_hash` = SHA-256 of `extracted_text` (unchanged by any offset repair).
- adapter `source_hash` = SHA-256 of `chunk.source_text` (`adapter.py:378`, unchanged).
- `original_hash` = SHA-256 of EPUB bytes (unchanged).
- chunker emits no hash of its own; `chunk_id` derives from `chapter_id` +
  `chunk_sequence` only.

No repair of the validator changes any hash or identity.

### 9.4 Recovery / resume

Resume state is keyed by `chapter_id:chunk_sequence` and reuses on `source_hash`
(`adapter.py:376-404,598-604`). **Offsets are not written to resume state** and are not
part of recovery eligibility. Offset repair does not touch the recovery schema or
identity.

### 9.5 Security

The defect and repair are confined to chunk validation. No ZIP guard, path
normalization, resource validation, or manifest validation is weakened. Security posture
unchanged.

### 9.6 TXT isolation

No offset helper is shared with TXT. The `extracted_*`/`body_*` fields exist only in
`core/epub_translation/*` and `core/adapters/epub_extraction_boundary.py`; nothing in
`lts/` or the TXT runtime references them. TXT requires **no change**.

## 10. Existing tests — why the defect was missed

| Test suite | Why it passed |
|------------|---------------|
| `tests/contract/test_s2_epub_chunking.py` | Exercises the chunker and codifies **body-relative** chunk body offsets, but **never calls `validate_epub_translation_chunk` / `validate_chunk_ownership`**. |
| `tests/contract/test_s1_epub_contract.py` | Validates rules but its chunk fixture uses `body_* == extracted_*` (marker-0-equivalent), so range and position both agree. |
| `tests/contract/test_s3_epub_runtime.py` | Every fixture chunk is built with `body_* == extracted_*`; the real adapter's validation therefore passes. |
| `tests/e2e/test_s10_03_*`, `test_s11_04/07`, `tests/integration/test_s11_*` | Call `chunk_epub_translation_input` and then feed a **deterministic injected runtime** (`deterministic_epub_runtime`), bypassing the real `translate_epub_translation_input`. |
| `tests/ui/test_s6_03_acceptance.py` | Mocks `EpubExtractionBoundary.extract` with fabricated offsets and mocks the packager/reader map. |

The real adapter's `validate_chunk_ownership` was never exercised end-to-end on
marker-prefixed chunker output. S12-04 was the first real-adapter run and surfaced it.

## 11. Canonical Offset Contract

**Decided from repository evidence (prior accepted decision + model invariant + chunker
design + S2 tests), not from ease of repair:**

```text
Canonical Offset Contract (EpubTranslationChunk):
  extracted_start_offset / extracted_end_offset
      = absolute code-point offsets into extracted_text (marker-inclusive, Space C),
        0-based, half-open [start, end), length = end - start.

  body_start_offset / body_end_offset
      = chapter-body-relative code-point offsets (Space B), 0-based,
        half-open [start, end), where 0 = chapter body start.
        Invariant: body_range == extracted_range for non-empty chunks;
                   body_range == 0 allowed for empty-body chunks.

  (On EpubChapterBoundary, body_start_offset/body_end_offset remain absolute in
   extracted_text — a different model with a different, documented meaning.)
```

This is "Option 1: body offsets are chapter-body-relative" plus the explicit
distinction that chapter-boundary body offsets are absolute.

## 12. Root Cause Classification

```text
Class B — Validator compares incompatible coordinate spaces.
```

- Not A (chunker wrong space): the chunker intentionally and consistently emits
  chapter-body-relative `body_*`, matching the model invariant, S2 tests, and the S5
  accepted semantics.
- Not C (extraction inconsistent): extraction is self-consistent absolute.
- Not D (adapter transforms/consumes incorrectly): the adapter does not reinterpret
  offsets; it only calls the validator.
- Not E (model internally inconsistent): the model enforces the correct invariant; its
  comments are ambiguous (documentation debt) but not functionally inconsistent.
- Not F (fixture invalid): the failure is on a real production EPUB through the real
  adapter path (S12-04 + this reproduction).

Contributing (non-root) factor: contract documentation debt from the reuse of the name
`body_start_offset` for two different spaces (E-adjacent, tracked for S12-06 docs only).

## 13. Decision

```text
REPAIR
```

Minimal, single-owner repair in the validator (`validation.py`), specified in the
companion design artifact. STOP conditions A–J are not triggered: the authoritative
coordinate space is established (not A/B), no schema change (not C), no runtime redesign
(not D), TXT untouched (not E), no provider/model change (not F), no security weakening
(not G), the defect reproduces without glossary (not H), it is not fixture-only (not I),
and a single offset algorithm remains (not J).

## 14. Pre-existing dirty state / diff hygiene

Preserved exactly (no stage, no restore):

```text
 M memory/character_memory_lts.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md      (deleted state kept)
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_S11_01_CAPABILITY_MATRIX.md
?? artifacts/NTPE_S11_01_POST_S10_PRODUCT_CAPABILITY_QUALITY_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_DESIGN.md
```

No `git add .` / `git add -A`. Only the two S12-05 artifacts are staged explicitly.

## 15. Execution accounting

```text
Provider Execution        : 0
Network Execution         : 0
Real Translation          : 0
Production Files Modified : NO
Tests Modified            : NO
Schema / Runtime / Legacy : unchanged
Temporary diagnostics     : created under D:\Temp\kilo (outside repo), removed, not committed
```

## 16. Acceptance Matrix

| Gate | Requirement | Result |
|------|-------------|--------|
| Baseline | `e4ad350` | PASS |
| Independent Reproduction | PASS | PASS |
| No Glossary | defect reproduced | PASS |
| Field Trace | complete | PASS |
| Coordinate Space | explicit | PASS |
| Inclusivity | explicit | PASS |
| Extraction | audited | PASS |
| Chunking | audited | PASS |
| Validator | audited | PASS |
| Adapter | audited | PASS |
| First Failure | identified | PASS (validator) |
| Root Cause | evidence-backed | PASS (B) |
| Canonical Contract | decided | PASS |
| Downstream | audited | PASS |
| Hash | audited | PASS |
| Recovery | audited | PASS |
| TXT | isolated | PASS |
| Security | unchanged | PASS |
| Test Gap | identified | PASS |
| Real Adapter E2E | future test defined | PASS (DESIGN §5) |
| Production Changes | NO | PASS |
| Tests Modified | NO | PASS |
| Provider / Network / Real Translation | 0 / 0 / 0 | PASS |
| Legacy | untouched | PASS |
| Dirty State | preserved | PASS |
| Artifact | complete | PASS |
| Decision | evidence-backed | REPAIR |

*End of audit.*
