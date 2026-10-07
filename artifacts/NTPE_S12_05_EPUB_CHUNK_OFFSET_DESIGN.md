# NTPE S12-05 — EPUB Chunk Offset Contract Minimal Repair Design

Design only. No production or test change is made by S12-05. This bounds S12-06.

## 0. Inputs

- Audit: `artifacts/NTPE_S12_05_EPUB_CHUNK_OFFSET_AUDIT.md`
- Canonical contract (§11 of audit):

```text
EpubTranslationChunk.extracted_start/end_offset : absolute in extracted_text (Space C)
EpubTranslationChunk.body_start/end_offset      : chapter-body-relative (Space B)
invariant: body_range == extracted_range (non-empty); body_range == 0 allowed
```

- Root cause: Class B — `validate_epub_translation_chunk` compares Space B against Space C.

## 1. Single Owner

The chunker is compliant with the canonical contract; the model is compliant. The only
non-compliant layer is `core/epub_translation/contract/validation.py`
(`validate_epub_translation_chunk`). Per the single-owner preference, the repair lives in
the validator only. No chunker change, no adapter change, no model change.

## 2. Exact semantic change

File: `core/epub_translation/contract/validation.py`
Function: `validate_epub_translation_chunk` (currently lines ~176-203)

Remove the two cross-coordinate comparisons that compare Space B to Space C:

```python
# DELETE (invalid cross-space checks)
if chunk.body_start_offset < chunk.extracted_start_offset: raise ...
if chunk.body_end_offset > chunk.extracted_end_offset: raise ...
```

Replace with the correct same-contract invariant already encoded by the model:

```python
# Same-contract cross-field invariant (no cross-space comparison).
body_range = chunk.body_end_offset - chunk.body_start_offset
if body_range != 0:
    extracted_range = chunk.extracted_end_offset - chunk.extracted_start_offset
    if body_range != extracted_range:
        raise ContractValidationError(
            f"chunk body range ({body_range}) must equal extracted range ({extracted_range})"
        )
```

Keep unchanged: id/order/sequence checks, non-negative checks, and
`extracted_end >= extracted_start`, `body_end >= body_start`.

This is **not** a loosening of the gate: it deletes an invalid comparison and asserts the
real contract relation (range equality), which the current validator fails to check at
all. The validator's other cross-field check in `validate_chunk_ownership` (extracted
offsets within the chapter's marker-inclusive `start/end`) is already space-correct and is
retained.

### 2.1 Why not fix the chunker instead

Changing the chunker to emit absolute `body_* = extracted_*` would:
- contradict the prior accepted semantics
  (`NTPE_S5_VALIDATION_DEFECT_REPAIR_01_REPORT.md` §2.3),
- contradict `EpubTranslationChunk.__post_init__`'s deliberate cross-coordinate design,
- break `tests/contract/test_s2_epub_chunking.py::TestOffsetIntegrity`,
- make `body_*` a redundant duplicate of `extracted_*`, losing the distiction the model
  invariant exists to protect.

So the validator, not the chunker, owns the fix.

### 2.2 Why no new offset converter

Repository search found no reusable absolute<->relative offset helper (audit §19-equivalent
grep). The chunker's inline conversion is sufficient and unchanged. No second conversion
helper is introduced (respects the "single algorithm" constraint, STOP-J).

## 3. Fields change / stay

| Field | Change |
|-------|--------|
| `EpubTranslationChunk.body_start_offset` / `body_end_offset` | semantics unchanged (chapter-body-relative); validator comparison corrected |
| `EpubTranslationChunk.extracted_start_offset` / `extracted_end_offset` | unchanged |
| `EpubChapterBoundary.body_*` / `start_offset` / `end_offset` | unchanged (absolute in extracted_text) |
| chunker output | unchanged |
| adapter | unchanged (already offset-agnostic) |
| packaging / reader map | unchanged |

## 4. Risk and rollback

- Risk: LOW. One comparison block in one pure function; no runtime, schema, provider, or
  I/O. Correctness is anchored by the model's existing invariant and S12-04 evidence.
- Residual risk: the validator loses the (invalid) claim that body offsets lie inside the
  extracted range. This does not reduce real coverage, because `validate_chunk_ownership`
  constrains `extracted_*` to the chapter and the chunker constrains `extracted_*` to the
  chapter body (`chunking.py:286-301`).
- Rollback: revert the single function body; no data migration, no state to rebuild.

## 5. Test design (implemented in S12-06, not here)

All offline/deterministic; no provider/network/real translation. Real-adapter tests must
**not** inject `engine`/`RuntimeOrchestrator.execute`; use `dry_run=True` or inject only
at the provider boundary.

### Test A — marker prefix + normal multi-chapter EPUB → chunk contract valid
Build ≥2 chapters via real `EpubExtractionBoundary`, real intake, real
`chunk_epub_translation_input`; assert `validate_chunk_ownership` passes and every chunk
satisfies `body_range == extracted_range` and
`extracted_text[extracted_start:extracted_end] == source_text`.

### Test B — no-marker / compatible offsets → existing contract preserved
Zero-length-marker fixture (or chapter `body_* == start/end`); assert validation passes and
offsets are unchanged from pre-repair behavior.

### Test C — real `translate_epub_translation_input` proceeds past the validator
Call the real adapter with `dry_run=True` (no engine injection). Assert it returns a
`EpubTranslationResult` with the expected chapter/chunk counts and does **not** raise
`ContractValidationError`. This is the minimal real-adapter regression that S12-04 lacked.

### Test D — offset/content mapping remains correct
For every chunk, assert
`extracted_text[extracted_start:extracted_end] == source_text` and
`chapter_body_text[body_start:body_end] == source_text`.

### Test E — chapter identity / source hash unchanged
Assert `original_hash`, `extracted_hash`, and adapter `source_hash`
(`sha256(source_text)[:16]`) equal pre-repair values; offsets are not inputs to any hash.

### Test F — recovery / resume unchanged
Run the adapter twice with resume enabled; assert none of `resume_state["chunks"][key]`
contains an offset key, and a second run reuses on `source_hash` identically.

### Negative/regression guards
- Constructing a chunk with `body_range != extracted_range` must still fail (model raises;
  validator also raises). Proves the gate is not merely relaxed.
- The existing S1/S2/S3 contract suites must remain green.

## 6. Real-adapter E2E requirement for S12-06

S12-04 proved that injected deterministic runtimes mask this defect. S12-06 must include at
least one **non-injected real `EpubTranslationAdapter`** execution leg:

```text
extract -> intake -> EpubTranslationInput -> chunk_epub_translation_input
-> translate_epub_translation_input(options with dry_run=True)   # real adapter, no engine injection
```

Optionally, a full non-dry-run leg with the provider replaced only at the provider call
boundary (still no network/real translation). The shared Qt E2E session's pre-existing
Windows access violation must be avoided by placing this in
`tests/integration/` (non-UI), as S12-04 did; it must not be fixed here.

## 7. Out of scope (explicitly not part of the minimal repair)

- No change to `validate_chunk_ownership` (optional future hardening: also bound
  `extracted_*` by `chapter.body_start_offset/body_end_offset` when present).
- No change to the ambiguous `EpubTranslationChunk` field comments (documentation debt;
  optional S12-06 comment-only clarification, no semantic effect).
- No TXT, runtime, recovery, provider, model, schema, or security change.
- No change to S11-closed ordering / non-linear / TOC logic.

## 8. STOP-condition check

```text
STOP-A authoritative space unknown        -> NOT triggered (decided)
STOP-B no conversion contract             -> NOT triggered (single contract; validator fixed)
STOP-C schema change                      -> NOT triggered
STOP-D runtime redesign                   -> NOT triggered
STOP-E TXT architecture                   -> NOT triggered
STOP-F provider/model change              -> NOT triggered
STOP-G security weakening                 -> NOT triggered
STOP-H glossary-related                   -> NOT triggered (reproduced without glossary)
STOP-I fixture invalidity only            -> NOT triggered (real production path)
STOP-J multiple competing algorithms      -> NOT triggered
```

Decision: **REPAIR** — proceed to S12-06 with the single-file validator fix plus the
real-adapter regression suite above.

*End of design.*
