# TIC Batch 5 — Historical Human Evidence Expansion

## Search scope and admission

Batch 5 scans only repository-preserved review, defect, release, and literary-evaluation files under the documented allowlist. Automatic metrics, unknown or incomplete reviews, test/release success, and praise keywords without complete human provenance and exact bilateral excerpts cannot be promoted. Batch 1 through Batch 4 artifacts are immutable SHA-256 anchors and are not rebuilt.

## Stage 11 priority evidence

Six Stage 11 defects have explicit human provenance. TQ-DEF-A reports Korean `인간` and translation `相當理性的人間`. The Korean token occurs twice in the full Batch 2 source and therefore cannot be selected by global similarity. The repository-preserved Stage 12.2.3 source freeze explicitly references TQ-DEF-A and SHA-locks source range `[0,153)`; within that range the token occurs exactly once. Combined with the unique translation excerpt, this creates one deterministic high-confidence `manual_evidence_anchor` overlay without guessing or changing Batch 3.

The existing evidence `TIC-EVID-B3-4C47ECCEDCAB1775DE59` is therefore completed for the TQ-DEF-A lexical defect. Five other Stage 11 defects remain unresolved because one or both reported excerpts are absent from, non-unique in, or not literal text of the immutable Korean/translation Case. Their reported text, match counts, attempted files, and future action remain in `UNRESOLVED_HUMAN_EVIDENCE.json`.

## Failure Corpus V2

The original Batch 4 subject-reference-shift case is copied byte-for-byte at canonical case-object level and retains its ID, evidence, alignment, text, offsets, SHA, category, and semantic constraint. One new human-confirmed `lexical_choice` case is added from TQ-DEF-A. The V2 corpus therefore contains two cases: one preserved and one new.

No root-cause analysis is performed and no corrected translation is generated. Suggested revisions in Stage 11 remain suggestions and are not approved output.

## Future excellence evidence

The search reviewed praise keywords but found no provenance-complete, precisely bilateral human praise evidence. The future-excellence candidate artifact is empty, `usable_for_future_excellence_corpus` is never inferred, and no Excellence Corpus is created.

## Boundaries

Provider, Runtime, Prompt, Stage 11/12, Golden Corpus, historical translations, and Batch 1–4 artifacts remain unchanged. No network request, Provider execution, new translation, corrected translation, root-cause analysis, or quality-improvement claim occurs. TIC Batch 6 has not started.
