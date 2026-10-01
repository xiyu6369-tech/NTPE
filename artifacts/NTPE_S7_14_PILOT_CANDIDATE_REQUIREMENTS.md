# NTPE S7-14 Pilot Candidate Requirements

**Dependency class**: `CANDIDATE_OUTPUTS`
**Current status**: PARTIAL — machine outputs exist; approved labeled bundles do not.

S7-14 forbids live provider generation.

---

## 1. Required per-candidate fields

`candidate_id`, `source_id`, `source_span_id`, `candidate_text`, `candidate_origin`,
`model`, `provider`, `prompt_version`, `runtime_version`, `attempt_number`,
`temperature`, `max_tokens`, `configuration_hash`, `timestamp`, `provenance`.

## 2. Allowed candidate origins

- Existing approved offline output
- Previously generated output
- Human-edited candidate
- Known-failure candidate (controlled)

## 3. Forbidden in S7-14

- Live provider generation
- Real translation
- Presenting machine output as a human reference

## 4. Diversity requirements (from S7-09 §9)

- Quality tiers: Clearly Good / Acceptable / Borderline / Clearly Poor
  (proportions `PRE-REGISTERED TARGET`).
- Failure-mode coverage: literalness, omission, hallucination, wrong terminology,
  wrong character identity, register mismatch, dialogue unnaturalness, repetition,
  formatting, context discontinuity.

## 5. Metric-leakage guard

`candidate selection must be independent of PS-03` (`selection_independent_of_ps03`),
so the human study is not circular with the metric under test.

## 6. Pairwise bundles

Best Attempt / Context / Segment Merge / Reviewer–Editor–ACE pairwise studies require
**approved offline candidate pairs**. None currently exist → those studies are
`NOT EXECUTED — NO APPROVED OFFLINE CANDIDATES`.
