# NTPE S7-15 Candidate Output Acquisition Specification

**Dependency**: `CANDIDATE_OUTPUTS`
**Current status**: SPECIFICATION READY (machine outputs exist; approved bundles do not)
**Extends**: `artifacts/NTPE_S7_14_PILOT_CANDIDATE_REQUIREMENTS.md` (KEEP / EXTEND)

S7-15 generates **zero** new translations.

---

## Required Fields

`candidate_id`, `source_id`, `source_hash`, `candidate_text`, `origin`, `model`,
`provider`, `prompt_version`, `runtime_version`, `attempt_id`, `generation_timestamp`.

## Allowed Origins

existing approved outputs · previously generated outputs · human-edited candidates ·
known-failure candidates (controlled).

## Forbidden in S7-15

new real translation · live provider generation · machine output declared human reference.

## Diversity (future pilot set)

clearly acceptable · borderline · clearly poor, plus relevant failure modes.
`Do not manufacture candidate outputs in S7-15.`

## Metric-Leakage Guard

`selection_independent_of_ps03` required so the study is not circular with PS-03.

## Acceptance

`ACCEPTED` only with complete provenance + source hash + origin. Until then: PARTIAL.
