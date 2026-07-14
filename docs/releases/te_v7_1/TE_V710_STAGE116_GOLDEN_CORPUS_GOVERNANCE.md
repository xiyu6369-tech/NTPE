# TE v7.1 Stage 11.6 — Golden Corpus Governance

Stage 11.6 adds an isolated governance contract for Golden Corpus case lifecycle, human approval, immutable source evidence, revisions, supersession, deprecation, rejection, integrity, and append-only audit history. It does not modify the existing Golden Review Corpus.

The lifecycle is `draft`, `under_review`, `approved`, `superseded`, `deprecated`, or `rejected`, with explicit fail-closed transitions. Approval is permitted only from `under_review` and requires a separate `human_governance_review` action, a non-empty approved translation, human provenance and reason, an accepted Stage 11.5 decision, and matching source/review/metrics/defects integrity references.

An accepted review decision is only an approval prerequisite. It is not Golden Corpus approval and cannot automatically populate `approved_final_translation`. Metrics, defects, plans, runtime results, Provider results, benchmarks, comparisons, models, or system automation cannot approve a case.

Source evidence remains immutable. Changes create a numbered revision with a previous-revision link; approved content changes return through draft, review, and approval. Supersession requires a different approved target and preserves both records. Deprecation and rejection are terminal governance actions with human provenance and substantive reasons.

The six existing corpus cases remain unchanged and every `approved_final_translation` remains `null`. This stage creates zero approved cases and adds zero approved translations. Its artifact fixture is explicitly `fixture`, `test_only`, `example`, and `not_applied`.

No prompt, Prompt Builder, Runtime, Provider, translation strategy, timeout, retry, baseline, candidate, comparison, or readiness behavior is changed. No network request or real translation is performed. TE v6 frozen layers remain unchanged, and Stage 11.7 is not started.
