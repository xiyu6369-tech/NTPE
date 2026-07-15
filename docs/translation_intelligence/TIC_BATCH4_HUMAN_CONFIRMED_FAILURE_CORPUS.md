# TIC Batch 4 — Human-Confirmed Failure Corpus

## Definition and scope

This initial corpus contains only human-confirmed failures with precise bilateral source/translation alignment. It is active but does not claim to represent every NTPE translation error, and it does not establish that translation quality has improved. TIC Batch 5 has not started.

## Strict admission

A case is admitted only when its Batch 3 unit is labeled `human_confirmed_failure`, has complete human provenance, non-empty source and translation text, source and translation overlap of `1.0`, exact or high alignment confidence, a bilateral alignment type, explicit category and traceable evidence/case/alignment IDs, complete offsets, and verified text SHA-256. Batch 1 through Batch 3 SHA anchors are checked before construction; any mismatch fails closed.

Automatic or unknown evidence, unreviewed units, unilateral units, Case-level-only links, imprecise alignments, and metrics findings are excluded. No repository rescan or Batch 1–3 rebuild occurs.

## Current corpus

The only admitted case is `TIC-EVID-B3-SUBJECT-SHIFT-001`, categorized strictly as `subject_reference_shift`. The translation assigns understanding of the situation to 鄭泰義, while the Korean assigns it to the previously mentioned distant man. The semantic constraint requires that this subject remain the distant man and not 鄭泰義.

Severity is `unspecified` and `blocking=false` because the human evidence provides neither an explicit severity nor a blocking decision. No broader category or subcategory is inferred.

## Excluded candidates

`TIC-EVID-B3-4C47ECCEDCAB1775DE59` is preserved as `linked_but_not_aligned` and excluded for `missing_source_excerpt`. The automatic Stage 11 metrics evidence and the unknown/incomplete Stage 12.2.3 review are also explicitly preserved in `EXCLUDED_FAILURE_CANDIDATES.json`; they are not silently discarded.

## No root cause, correction, or excellence corpus

Root-cause analysis is not performed: `root_cause_status=not_analyzed` and `root_cause=null`. No corrected translation is generated: `corrected_translation_status=not_provided` and `corrected_translation=null`. Because Batch 3 has zero human-confirmed excellence units, `excellence_corpus_created=false`.

## Limitations and boundaries

The corpus begins with one precisely anchored case and must grow only through future repository-preserved human evidence. Provider, Runtime, Prompt, historical translations, Golden Corpus, and Batch 1–3 artifacts remain unchanged. Network requests, new translations, corrected translations, and quality claims all remain zero or false.
