# NTPE S7-15 External Resource Dependency Status

**As of**: 2026-09-30 (specification phase; no resources acquired)

## Status Taxonomy

`MISSING · SPECIFIED · SUBMITTED · VALIDATING · ACCEPTED · REJECTED · EXPIRED`
`SPECIFIED` is never reported as `AVAILABLE`.

## Dependency Status

| Resource | Current Status | Required Artifact | Validation | Available | Pilot Blocking |
|----------|----------------|-------------------|------------|-----------|----------------|
| Human Evaluators | UNAVAILABLE | evaluator roster | qualification | NO | **YES** |
| Reference Data | MISSING | reference corpus | provenance/review | NO | **YES** |
| Character Arc | EXTERNAL_DEPENDENCY | annotation set | schema/provenance | NO | Calibration-dependent |
| Pilot Corpus | SPECIFIED | manifest | offline validation | NO | **YES** |
| Candidates | SPECIFIED | manifest | provenance | NO | **YES** |
| Blinding | READY | blinding contract | verified | YES | YES (must VERIFY at pilot) |
| Randomization | READY | randomization contract | verified | YES | YES (must VERIFY at pilot) |
| Provenance | READY | provenance schema | verified | YES | YES (must VERIFY at pilot) |

## Acceptance Owner

| Responsibility | Owner |
|----------------|-------|
| Creation | External supplier |
| Review | TBD |
| Approval | TBD |
| Import | TBD |
| Audit | TBD |

Where the project has no assigned personnel, `OWNER = TBD`; this is an ownership
dependency, not an implementation defect.

## Statement

Human evaluators and reference data are **not available** and must not be represented as
available. All three core dependencies remain open.
