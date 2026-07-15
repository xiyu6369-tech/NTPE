# TIC Batch 3 — Manual Evidence Linking and Fine-Grained Alignment

## Scope

Batch 3 links repository-preserved evidence to the 125 immutable Batch 2 translation cases, segments Korean source and Traditional Chinese translation text, and creates deterministic preliminary alignment units. It does not rebuild Batch 1 or Batch 2, call a Provider, generate or revise translation, perform root-cause analysis, or create a Failure/Excellence Corpus. TIC Batch 4 has not started.

## Evidence and human provenance

The inventory includes human-confirmed Stage 11 defects, automatic Stage 11 metrics, the incomplete Stage 12.2.3 manual-review template, and the repository-preserved Batch 3 user review for the known subject-reference shift. `reviewer_type` distinguishes `human`, `automatic`, `mixed`, and `unknown`. A failure/excellence usability flag may be true only when the reviewer is human and `human_provenance.complete=true`. Automatic metrics never substitute for human evidence. Ambiguous or absent matches remain `ambiguous` or `unlinked`.

The known Stage 12.2.3 baseline case is linked by exact translation path and exact source/translation excerpts. The human finding is `subject_reference_shift`: the distant man is the person who understands the situation, not 鄭泰義. No corrected translation is generated or approved.

## Segmentation

Korean and Traditional Chinese segmentation first preserves blank-line paragraph boundaries and then uses language-specific sentence endings. Quote and bracket stacks prevent a split inside protected spans; a terminal inside dialogue is emitted only after its closing quote. Original codepoints, whitespace, order, Unicode-codepoint offsets, and SHA-256 are retained. Segments are typed as `narrative`, `dialogue`, `mixed`, or `unknown`.

## Alignment

Alignment is deterministic and bounded by corresponding paragraph order. Equal sentence-group counts align one-to-one. Unequal counts remain one-to-many, many-to-one, or many-to-many inside the paragraph. Extra paragraphs become source-only or translation-only units; no remainder is globally merged, reordered, deleted, normalized, or similarity-forced. The implementation also preserves an explicit unresolved form.

Allowed quality labels are `human_confirmed_failure`, `human_confirmed_excellence`, `human_reviewed_neutral`, `unreviewed`, and `insufficient_evidence`. Only an exact, conflict-free link with complete human provenance can apply a human-confirmed label. No automatic excellence is created, and a whole-document PASS cannot be expanded into segment-level excellence.

Failure evidence is applied to an alignment unit only when that same unit fully covers both the evidence source excerpt and translation excerpt at their preserved offsets, both overlaps equal `1.0`, both texts are non-empty, the unit is not source-only/translation-only/unresolved, and the human-confirmed link confidence is exact or high. Case ID, file path, or neighboring paragraphs alone never propagate a failure label. Evidence lacking either side remains `linked_but_not_aligned`.

When no ordinary unit covers both sides, the generator creates one deterministic `manual_evidence_anchor` overlay from only the source and translation segments needed to cover the excerpts. The overlay has high confidence, preserves original text and offsets, and is marked `evidence_overlay=true` and `coverage_eligible=false`. The known subject-reference shift therefore has exactly one confirmed overlay unit. Stage 11 defect evidence that has only a translation excerpt remains linked to its Case but does not label any alignment unit.

## Coverage

`alignment_coverage = coverage_eligible_units_with_both_source_and_translation / all_coverage_eligible_alignment_units`.

The denominator includes ordinary `unresolved`, `source_only`, and `translation_only` units. Evidence overlays are explicitly excluded because they reuse existing segments and would otherwise duplicate coverage. Therefore unmatched content lowers coverage and cannot be hidden to inflate the result.

## Artifacts and boundaries

The evidence inventory, links, segments/alignment units, statistics, search index, and SHA-256 manifests live under `artifacts/tic_batch3/` and `manifests/`. The index supports the requested case, corpus, file, stage, model, segment, alignment, review, quality, failure, and evidence metadata. It is a JSON index, not a full-text engine or vector database.

Boundary values: `provider_executed=false`, `network_requests=0`, `new_translation_generated=false`, `historical_translation_modified=false`, `runtime_modified=false`, `provider_modified=false`, `prompt_modified=false`, `stage11_modified=false`, `stage12_modified=false`, `golden_corpus_modified=false`, `batch1_inventory_rebuilt=false`, `batch2_cases_rebuilt=false`, `failure_corpus_created=false`, `excellence_corpus_created=false`, `root_cause_analysis_executed=false`, and `tic_batch4_started=false`.
