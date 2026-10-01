# NTPE S7-15 Pilot Manifest Schema

Defines the versioned manifest that must be complete and self-consistent before any future
pilot task starts. S7-15 does not populate it.

---

## Manifest Header

| Field | Purpose |
|-------|---------|
| `pilot_id` | unique pilot identifier |
| `protocol_version` | evaluation protocol version (e.g., v1.1) |
| `rubric_version` | rubric version |
| `corpus_version` | corpus version |
| `candidate_version` | candidate set version |
| `reference_version` | reference set version (nullable if reference-free) |
| `evaluator_version` | evaluator roster/protocol version |
| `randomization_version` | randomization scheme version |
| `provenance_version` | provenance schema version |

## Package References

Seven entry packages, each with a manifest reference + hash:

1. Evaluator Package
2. Reference Package
3. Corpus Package
4. Candidate Package
5. Blinding Package
6. Randomization Package
7. Provenance Package
8. Analysis Package

## Manifest Acceptance

A pilot may start only when:
- all required artifacts are available,
- all hashes are valid,
- all versions are compatible,
- all dependencies are satisfied.

## Dependency Snapshot (must be `ACCEPTED` before start)

| Dependency | Required state |
|------------|----------------|
| Human evaluators | ACCEPTED |
| Reference data | ACCEPTED (or reference-free explicitly declared) |
| Character-arc annotation | ACCEPTED or documented non-blocking limitation |
| Pilot corpus | ACCEPTED |
| Candidates | ACCEPTED |
| Blinding | VERIFIED |
| Randomization | VERIFIED |
| Provenance | VERIFIED |
| R1 / R3 | CLOSED |

## Status Codes

`MISSING · SPECIFIED · SUBMITTED · VALIDATING · ACCEPTED · REJECTED · EXPIRED`.
`SPECIFIED` must never be reported as `AVAILABLE`.
