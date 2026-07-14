# TE v7.1 Stage 11.1 — Translation Defect Classification

Stage 11.1 converts the six human-confirmed Stage 10.10.1 review findings into stable, serializable defect records. Each record has one primary category, optional secondary categories, stable severity ordering, minimal excerpts, review provenance, and an explicit blocking flag.

The accompanying Golden Review Corpus contains only the same reviewed cases. `preferred_direction` is guidance, not an approved translation, and every `approved_final_translation` remains `null`.

Boundaries: no Provider execution, network request, new translation, prompt modification, runtime modification, or automatic correction.
