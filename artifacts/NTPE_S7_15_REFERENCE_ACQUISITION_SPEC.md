# NTPE S7-15 Reference Data Acquisition Specification

**Dependency**: `REFERENCE_DATA` — `EXTERNAL_DATA_DEPENDENCY`
**Current status**: `MISSING` (Specification = complete; Availability = NO)
**Extends**: `artifacts/NTPE_S7_14_REFERENCE_DATA_REQUIREMENTS.md` (KEEP / EXTEND)

S7-15 creates **zero** references. Machine outputs are never accepted as human references.

---

## Classes (unchanged)

| Class | Creator | Review | Calibration | Validation | Holdout |
|-------|---------|--------|-------------|------------|---------|
| GOLD | Professional/human translator | ≥2 independent reviews + adjudication | ✅ | ✅ | ✅ |
| SILVER | Human-edited MT | 1 review + approval | ⚠️ limited | ⚠️ limited | ❌ |
| BRONZE | Single human, no review | None | diagnostic only | ❌ | ❌ |

Standards must not be lowered at acquisition time.

## GOLD Requirements

human-created or human-validated · complete source coverage · literary review ·
terminology consistency · character consistency · source fidelity · provenance ·
independent review · approval. Must record: creator, reviewer, revision history, source
version, reference version.

## GOLD Acceptance (all required)

creator provenance · review evidence · source mapping · completion evidence.
Missing any → **not GOLD** (may be reclassified SILVER/BRONZE or REJECTED).

## SILVER / BRONZE

- SILVER: not automatically gold; allowed-use explicit.
- BRONZE: diagnostic/pilot-supporting/exploratory only; **not** a gold calibration reference
  without subsequent human validation.

## Role Separation

Roles: `Reference Creator`, `Reference Reviewer`, `Evaluator`, `Candidate Generator`.
Hard rule: `creator != evaluator` for the same evidence unit.

## Provenance (required per reference)

`reference_id`, `source_id`, `source_hash`, `source_version`, `reference_class`,
`creator_id`, `reviewer_id`, `review_status`, `coverage_status`, `revision_version`,
`creation_timestamp`, `approval_timestamp`.

## Source Alignment

`reference source == evaluated source` or an explicit mapping must exist. No "different
source, same reference label".

## Completeness

Check source/paragraph/sentence/segment completeness. Any incomplete reference → not GOLD.

## Contamination Rules

- No same-person creator+evaluator on the same evidence unit.
- `reference != candidate` must be distinguishable in provenance.

## Machine Translation Prohibition

`original_ko_zh.txt` or any machine output cannot become GOLD without conformant human
validation/review.

---

## Acceptance

`ACCEPTED` only with full provenance + review + source mapping + completion + role
separation + version + hash. Otherwise `REJECTED` or `REQUEST_REVISION`.
