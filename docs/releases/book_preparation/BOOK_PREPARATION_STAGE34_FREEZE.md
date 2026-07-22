# Book Preparation Pipeline — Stage 3.4 Freeze

## Scope

Stage 3.4 freezes the offline book-preparation work delivered by Stage 3.1 through Stage 3.3. Stage 3.1 provides conservative structure segmentation, Stage 3.2 provides deterministic translation-chunk planning, Stage 3.3 provides orchestration, and Stage 3.4 provides validation metadata, source hashes, compatibility evidence, and the activation gate.

Book Intake remains governed by its independent Stage 2 freeze.

## Pipeline architecture

```text
BookIntakeProcessor
  -> BookPreflightAnalyzer
  -> BookIntakeManifestBuilder
  -> BookStructureSegmenter
  -> BookChunkPlanner
  -> cross-stage validation
  -> BookPreparationResult
```

Every dependency is invoked at most once. `prepare_intake()` begins with Preflight and does not repeat Intake. Warnings never cause retries or fallback execution.

## Frozen public API

The freeze records 31 unique symbols exported by:

- `core.book_segmentation`
- `core.book_chunking`
- `core.book_preparation`

The Preparation package additionally exports `BookPreparationFreezeMetadata`, `BookPreparationFreezeValidationResult`, `BookPreparationFreezeValidationError`, `get_book_preparation_freeze_metadata`, and `validate_book_preparation_freeze`.

## Segmentation contract

Segmentation uses 0-based, half-open Python string offsets. Sections cover the complete source without gaps or overlaps and reconstruct it exactly. Heading detection remains conservative and deterministic. Front matter is retained, numeric-only headings require a confirmed sequence, and text without a reliable heading becomes one unclassified manual-review section.

## Chunk-planning contract

Default sizes are minimum 800, target 2000, and maximum 2600 characters. Boundary priority is paragraph, sentence, line, then hard limit. Chunks cover the source exactly, preserve section references and newline bytes at the Unicode-string level, never exceed the configured maximum, and do not split chapter headings or CRLF pairs. Hard splitting remains the last resort.

## Preparation orchestration contract

The orchestration order is fixed. Intake or Preflight blocking stops downstream work. Manual review may continue through offline analysis but cannot be downgraded to ready. Cross-stage text, source names, fingerprints, status/action metadata, and character/section/chunk counts fail closed on mismatch. Dependency failures retain exception chaining.

## Status and action contract

| Status | Action |
|---|---|
| `ready` | `proceed` |
| `ready_with_warnings` | `proceed_with_warning` |
| `manual_review` | `manual_review` |
| `blocked` | `reject` |

Aggregation priority is blocked, manual review, ready with warnings, then ready. Intake and Preflight naming variants are normalized without reducing severity.

## Fingerprint contract

Source fingerprints use SHA-256 over exact UTF-8 text without normalization. Segmentation, chunk-plan, and preparation fingerprints use deterministic canonical JSON with Unicode preserved, sorted keys, and compact separators. Each payload excludes its own resulting fingerprint. Newline or whitespace changes therefore change the relevant fingerprints.

## Determinism guarantees

Repeated execution produces identical segmentation results, section offsets, headings, chunk plans, boundary reasons, findings, status/action decisions, and fingerprints. Freeze validation returns immutable deterministic metadata and reads only the freeze manifest plus the 15 frozen Stage 3 source files.

## Content-preservation guarantees

Unicode text, CRLF/LF style, whitespace, combining characters, headings, front matter, paragraph separators, and terminal newlines are retained. Segmentation sections, translation chunks, and the preparation result each reconstruct the Intake text exactly.

## Error and fail-closed behavior

Hash drift, missing or extra inventory entries, API drift, schema drift, policy drift, and cross-stage inconsistencies raise explicit validation errors. Original Intake source and decoding errors remain identifiable. No validation failure is converted into a warning result.

## Security and privacy boundary

The pipeline is offline. Provider requests, network requests, translation executions, output-file writes, Runtime integration, Launcher integration, and Production hooks added by this freeze are all zero. Metadata, manifest, and evidence contain no timestamp, UUID, Git commit, hostname, username, absolute path, or novel content.

## Explicit non-capabilities

This freeze does not translate text, invoke a Provider, send chunks, activate automatic translation, connect Runtime or Launcher, add a Production Hook, or authorize production integration.

## Activation gate

The frozen activation gate is:

```text
book_preparation_pipeline_frozen
```

All authorization flags remain `false`. The gate records a completed offline foundation; it does not authorize translation execution.

## Validation commands

```powershell
python -m pytest tests\unit\book_preparation\test_freeze.py -q
python -m pytest tests\integration\book_preparation_freeze_test.py -q
python verification\book_preparation\book_preparation_stage34_freeze_acceptance.py
python -m pytest tests\unit\book_preparation -q
python -m pytest tests\integration\book_preparation_pipeline_test.py -q
python -m pytest tests\unit\book_chunking -q
python -m pytest tests\integration\book_chunking_segmentation_test.py -q
python -m pytest tests\unit\book_segmentation -q
python -m pytest tests\integration\book_segmentation_intake_test.py -q
python -m pytest tests\unit\book_intake -q
python -m compileall core\book_segmentation core\book_chunking core\book_preparation -q
python ntpe_validate.py
git diff --check
```

## Release state

Commit, Push, and Tag have not been executed. Stage 3.4 stops at the frozen offline preparation boundary.
