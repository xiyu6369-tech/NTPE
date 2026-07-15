# NTPE Translation Intelligence Corpus (TIC)

## Batch 1 - Historical Translation Corpus Inventory

TIC Batch 1 creates a deterministic, read-only inventory of translation evidence already present in the NTPE repository. It does not generate, repair, rank, or score translations.

## Scope

The scan covers `tests/literary`, `tests/literary/outputs`, `output`, `artifacts`, repository `Golden_Set` and `Passion` locations when present, all `translation.txt`, all `*_zh.txt` and partial variants, translation result caches, and the identified manual-review translation TXT. Missing optional top-level locations are recorded as absent instead of silently ignored.

Each inventory row records a deterministic Corpus ID, source and translation paths, stage and version evidence, provider and model evidence, chunk size, translation status, SHA-256 values, manual-review evidence, and quality-analysis usability. Unknown historical metadata is stated explicitly; it is never guessed.

## Status taxonomy

- `Completed Translation`: a non-empty completed artifact.
- `Partial Translation`: an artifact identified as partial by filename or manifest.
- `Provider Timeout`: an artifact whose preserved metadata records a timeout.
- `Manual Reviewed`: a translation linked to completed human-review evidence.
- `Historical Translation`: the common historical-evidence tag and the primary status for a preserved placeholder with no completed translation.

No Failure Classification is created in this batch. Status labels only describe preserved execution or review state.

## Artifacts

- `artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json`
- `artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json`
- `artifacts/tic_batch1/TRANSLATION_CORPUS_MANIFEST.json`
- `manifests/tic_batch1_translation_corpus_inventory_manifest.json`

The inventory and statistics use canonical sorted JSON. Corpus IDs derive from repository-relative artifact paths, and every source or translation SHA-256 is computed from existing bytes. Rebuilding against unchanged repository evidence produces identical output.

## Boundaries

- Inventory only; no Framework expansion.
- No Provider or network execution.
- No new translation and no translation modification.
- No Runtime, Prompt, timeout, retry, chunk, model, Stage 11, or Stage 12 modification.
- No quality scoring, Failure Corpus, Excellence Corpus, prompt improvement, root-cause analysis, or Translation Quality Recovery.

TIC Batch 1 Completed.

TIC Batch 2 Not Started.
