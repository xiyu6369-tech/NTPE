# NTPE Translation Intelligence Corpus (TIC)

## Batch 2 - Translation Case Extraction

TIC Batch 2 converts the historical translation artifacts selected by TIC Batch 1 into deterministic, analysis-ready Translation Cases. It does not scan the repository for new candidates and does not rebuild the Batch 1 Inventory or Statistics.

## Sole selection inputs

- `artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json`
- `artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json`

Every Case preserves its Batch 1 Corpus ID, source and translation references, stage, version, provider, model, file SHA-256 values, status, and review reference. Translation text is copied exactly from the referenced historical TXT or JSON result. No text is translated, repaired, normalized, scored, or classified.

## Extraction rules

- Completed, Partial, and Manual Reviewed artifacts with translation text become Translation Cases.
- Provider Timeout artifacts with preserved partial text become Partial-tagged Cases without changing their timeout status.
- Provider Timeout artifacts with no translation text become Execution Evidence only.
- Other empty placeholders do not become Cases or Execution Evidence.
- Inventory order is retained. Chunk IDs and indexes come from preserved filenames or evidence metadata.
- Chunk offsets are Unicode code-point ranges. Their basis is explicitly recorded as the Inventory source file, an Inventory source reference, or source embedded in the historical translation artifact.
- Document and partial-document Cases retain the recorded chunk count where it is available or deterministically infer it from Batch 1 Inventory entries in the same stream.

## Artifacts

- `artifacts/tic_batch2/TRANSLATION_CASES.json`
- `artifacts/tic_batch2/TRANSLATION_CASE_INDEX.json`
- `artifacts/tic_batch2/TRANSLATION_CASE_STATISTICS.json`
- `artifacts/tic_batch2/TRANSLATION_CASE_MANIFEST.json`
- `manifests/tic_batch2_translation_case_extraction_manifest.json`

The metadata-only Index supports Case ID, Corpus ID, Stage, Provider, Model, Translation Status, and Source File. Full-text search is not implemented in Batch 2.

## Boundaries

- No Runtime, Provider, Prompt, LiteraryPromptBuilder, Candidate, Stage 11, Stage 12, or Golden Corpus modification.
- No Provider execution and no new translation.
- No modification of historical translations.
- No quality judgement, Failure classification, Excellence classification, or Batch 3 analysis.

TIC Batch 2 Completed.

TIC Batch 3 Not Started.
