# NTPE S7-15 External Data Intake Specification

**Scope**: how ANY external resource (evaluator roster, reference, annotation, corpus,
candidates) is submitted, validated, quarantined, accepted, version-locked, or rejected.

---

## Intake Pipeline

```
Dependency Specification
        ↓
External Submission
        ↓
Quarantine
        ↓
Schema Validation
        ↓
Provenance Validation
        ↓
Role/Conflict Validation
        ↓
Quality Validation
        ↓
Acceptance  (version lock)
        ↓
Pilot Ready
```

## Submission Requirements

submission format · manifest · hash · version · provenance · quality checks ·
accept/reject decision · quarantine · revision path.

## Quarantine Rule

Every new resource is `QUARANTINED` until validated. Quarantined resources cannot enter
the pilot.

## Immutability

Once accepted, the accepted version must not be modified directly. Any change = new
version + new hash + new provenance + re-validation.

## Version Compatibility

`evaluator protocol` · `rubric` · `corpus` · `candidate` · `reference` versions must be
compatible. Rubric version mismatch → `REJECT / REVALIDATE`.

## Rejection

Reject (with recorded reason) on: missing provenance · role conflict · invalid schema ·
duplicate · source mismatch · version mismatch · quality failure.

## No Silent Repair

Never silently fix external data (e.g., filling missing evaluator-label fields). Missing
fields → `REJECT` or `REQUEST_REVISION`.

## Provenance Audit

Every accepted resource traceable to: origin · creator · reviewer · version · hash ·
approval.

## Security Boundary

Before import: file integrity · hash · schema · malicious-content scan (if available) ·
unexpected-executable-content check. Never execute unknown external scripts.

## Privacy Boundary

No personal contact details in repository artifacts; pseudonymous IDs only.

## Data Ownership

Define who may modify/approve/export/access raw/access derived. If undefined in the
project: `TBD` (do not assume).

## Rejection Workflow

```
Submission → Validation Failure → REJECT / REQUEST_REVISION → Record Reason → New Version → Re-validation
```
Forbidden: `failure → silently repair → accept`.
