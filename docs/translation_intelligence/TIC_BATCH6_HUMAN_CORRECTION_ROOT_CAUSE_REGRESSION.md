# TIC Batch 6 — Human Correction, Root Cause, and Quality Regression

## Scope

Batch 6 consumes the two frozen human-confirmed failures in TIC Failure Corpus
V2. Batch 1–5 artifacts are SHA-256 anchors and are not rebuilt or modified.
The new code is offline, deterministic, case-bound, and uses
`core.shared.evidence` for canonical JSON and hashing.

No production fix is applied. Runtime, Provider, Prompt, glossary, QA Engine,
translation strategy, historical translations, Stage 11, and Stage 12 remain
unchanged. No Provider or network request is executed, and Batch 7 is not
started.

## Corrections

### Subject reference shift

- Historical bad translation: `被拋在遠方的那個男人雖然像個怪物，但至少他仍然是個理智清醒的人，鄭泰義也明白這種情況不可能是他故意製造的。`
- Minimal draft: `被拋在遠方的那個男人雖然像個怪物，但至少他仍然是個理智清醒的人，他也會明白這種情況不可能是鄭泰義故意製造的。`
- Constraint: the distant man remains the cognitive actor; 鄭泰義 remains the
  negated actor of intentionally causing the situation.

### Lexical choice

- Historical bad translation: `相當理性的人間`
- Minimal draft: `相當理性的人`
- Constraint: `인간` denotes a human person in this fixed context; `人間` is
  forbidden.

Both corrections are `human_draft`. The repository contains human semantic
constraints, but no complete, exact, human-approved corrected wording. They
must not be promoted to `human_approved` until that approval exists.

## Root-cause findings

Both records are `evidence_supported`, not `human_confirmed`.

- Subject shift: the observed output changes the semantic actor, and existing
  offline QA did not guard this fixed case. The source also contains a distant
  antecedent followed by `그는`, which supports a long-distance resolution
  risk. Prompt causality and post-processing causality remain unproven. The
  minimum recommended fix location is a **semantic regression**.
- Lexical choice: the observed output uses a Korean/Chinese near-form lexical
  choice that is invalid for a person in the frozen context. A fixed-case
  Traditional Chinese lexical guard was absent. The minimum recommended fix
  location is a **lexical validator**.

These findings distinguish prompt, context, model output, post-processing, and
QA detection. They do not assume that the model alone caused either failure.

## Regression behavior

The evaluator is deliberately narrow and does not claim general Korean subject
resolution or global lexical replacement.

- Subject shift checks a required semantic actor, a forbidden cognitive actor,
  the unchanged intent actor, and the frozen situation semantics.
- Lexical choice checks the fixed `相當理性…` context, forbids `人間`, and allows
  only `人`, `人物`, or `人類` for this one case.

Both historical bad translations deterministically fail. Both drafts satisfy
their constraints, while unrelated text is rejected. Because neither draft is
yet human-approved, both regression cases remain
`pending_human_correction`; `approved_translation_passes` is intentionally
null rather than a fabricated PASS.

This batch creates a quality regression guard, but it does not prove complete
translation-quality improvement.

