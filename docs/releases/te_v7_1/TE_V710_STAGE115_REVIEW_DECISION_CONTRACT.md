# TE v7.1 Stage 11.5 — Human Review Decision Contract

Stage 11.5 adds an explicit, human-only decision record over the redacted Stage 11.3 review evidence. The contract accepts exactly four statuses: `accepted`, `rejected`, `needs_revision`, and `insufficient_evidence`. A decision is valid only when its source is `human_review`, its reviewer provenance is non-automated, its reason is substantive, and all three Stage 11.1–11.3 SHA-256 references match the files reviewed.

`accepted` is a human governance statement, not a score-derived result and not authorization to execute anything. Metrics, defects, the planner, Provider, Runtime, models, or system automation cannot create a valid accepted decision. The stage artifact contains one deterministic test fixture, explicitly marked `fixture`, `test_only`, `example`, and `not_applied`.

The Golden Review Corpus is unchanged and every `approved_final_translation` remains `null`. Stage 11.4 plans remain `planned_not_applied`; no prompt or prompt builder is edited. There is no Provider or network execution, no new translation, no baseline or candidate, no comparison or readiness evaluation, and no decision is applied.

Stage 11.5 is an isolated contract layer. It does not alter TE v6 frozen runtime behavior and does not start Stage 11.6.
