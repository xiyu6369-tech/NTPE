# TE v7.1 Stage 11.2 — Translation Quality Metrics

Stage 11.2 derives 0–100 quality metrics only from Stage 11.1 defect IDs, severities, blocking state, and human evidence. A critical blocking omission lowers completeness and applies a fail-closed overall cap. Dimensions without reviewed evidence are marked `insufficient_evidence` with a neutral placeholder and are never treated as full score.

The current artifact records `quality_pass=false`, `human_review_based=true`, `provider_execution_performed=false`, and `new_translation_generated=false`.
