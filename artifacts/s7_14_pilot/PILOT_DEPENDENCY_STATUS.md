# NTPE S7-14 Pilot Dependency Status

**As of**: 2026-09-30 (offline; no pilot executed)

| Dependency | Status | Required | Available | Blocking |
|------------|--------|---------:|----------:|---------:|
| Human evaluators | UNAVAILABLE (external resource) | Yes | No | **Yes** |
| Reference corpus (GOLD/SILVER/BRONZE) | MISSING (external data) | Yes | No | **Yes** |
| Pilot corpus | PARTIAL (sources exist; manifest unpopulated) | Yes | Partial | Yes (for full pilot) |
| Candidates | PARTIAL (machine outputs exist; approved bundles do not) | Yes | Partial | Yes (pairwise studies) |
| Protocol | READY (v1.1 + S7-14 policies) | Yes | Yes | No |
| Schema | READY (provenance/corpus schemas defined) | Yes | Yes | No |
| Provenance | READY (requirements defined) | Yes | Yes | No |
| Blinding | READY (contract + offline check) | Yes | Yes | No |
| Randomization | READY (contract + offline check) | Yes | Yes | No |

## Dependency Classes

| Class | Blocker | Nature |
|-------|---------|--------|
| `HUMAN_EVALUATOR` | A | `EXTERNAL_RESOURCE_DEPENDENCY` |
| `REFERENCE_DATA` | B | `EXTERNAL_DATA_DEPENDENCY` |
| `PILOT_CORPUS` | partial | repository-resolvable (selection) |
| `CANDIDATE_OUTPUTS` | partial | approved offline bundles needed |
| `EVALUATION_INTERFACE` | none | READY |
| `PROVENANCE` | none | READY |

## Statement

Human evaluators and reference data are **not** available and must **not** be
represented as available. These are external dependencies, not code defects.
