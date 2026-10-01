# NTPE S7-15 External Literary Evaluation Resource Acquisition Report

**Task**: `S7-15 External Literary Evaluation Resource Acquisition Specification`
**Date**: 2026-09-30
**Executor**: Kilo (Automated)
**Status**: `SPECIFICATION COMPLETE — RESOURCES NOT AVAILABLE`

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| Actual HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Branch | `main` |
| Upstream | `origin/main` (tracking; not modified) |
| Origin | `https://github.com/xiyu6369-tech/NTPE.git` |
| Working Tree | pre-existing modified/deleted/untracked — all preserved |

## 2. S7-14 Findings Consumed

`S7_14_READINESS_PACKAGE_COMPLETE_PILOT_EXTERNALLY_BLOCKED` consumed. Methodology R1/R2/R3
= `CLOSED_VERIFIED`; H02 = `EXTERNAL_DEPENDENCY`; pilot blocked by external
`HUMAN_EVALUATOR` + `REFERENCE_DATA`.

## 3. Scope

Convert the three external dependencies (A human evaluators, B reference data,
C character-arc annotation) into a formal acquisition / acceptance / intake contract.
No resources were acquired.

## 4. Human Evaluator Specification

`artifacts/NTPE_S7_15_HUMAN_EVALUATOR_ACQUISITION_SPEC.md`. Real-human definition,
minimum count 3–5 (pilot design target, not validated), qualification incl. `TBD` items
(no invented expert thresholds), role separation, blindness, session/fatigue (`TBD from
pilot`), privacy (pseudonymous id), withdrawal/replacement, qualification gate, exclusion
rules. Status: SPECIFIED; availability NO.

## 5. Reference Specification

`artifacts/NTPE_S7_15_REFERENCE_ACQUISITION_SPEC.md`. GOLD/SILVER/BRONZE unchanged;
GOLD acceptance requires creator provenance + review + source mapping + completion;
SILVER not auto-gold; BRONZE not gold calibration reference; role separation; required
provenance fields; source alignment; completeness; contamination rules; machine-translation
prohibition. Status: SPECIFIED; availability NO.

## 6. Character-Arc Annotation Specification

`artifacts/NTPE_S7_15_CHARACTER_ARC_ANNOTATION_SPEC.md`. Defines `character_arc_id`
semantics (same character ≠ same arc; multi-arc allowed), required fields, annotation
method (human/double/adjudication), reliability, split integration, acceptance/rejection.
Status: SPECIFIED; availability NO.

## 7. Pilot Corpus Specification

`artifacts/NTPE_S7_15_PILOT_CORPUS_ACQUISITION_SPEC.md`. 50 = `PILOT_ONLY`,
scene-level/chapter-aware, stratification coverage, manifest fields, acceptance criteria.

## 8. Candidate Specification

`artifacts/NTPE_S7_15_CANDIDATE_OUTPUT_ACQUISITION_SPEC.md`. Required provenance fields,
allowed origins, no live generation, diversity, metric-leakage guard, acceptance.

## 9. External Data Intake

`artifacts/NTPE_S7_15_EXTERNAL_DATA_INTAKE_SPEC.md`. Submission/manifest/hash/version/
provenance, quarantine, immutability, version compatibility, rejection, no-silent-repair,
provenance audit, security/privacy boundary, ownership (`TBD` where undefined).

## 10. Validation / Quarantine

Every new resource is `QUARANTINED` until validated. Accepted resources are version-locked;
any change = new version + new hash + new provenance + re-validation.

## 11. Role Separation

Reference Creator ≠ Evaluator ≠ (Study Administrator / Data Analyst as applicable). Enforced
by `creator_id` vs `evaluator_id` disjointness.

## 12. Privacy / Security

Pseudonymous IDs only; no personal contact details in repository artifacts. Import checks:
integrity/hash/schema/malicious-content/unexpected-executable; never execute unknown scripts.

## 13. Versioning / Immutability

Versioned + hash-locked resources; rubric version mismatch → `REJECT / REVALIDATE`.

## 14. Dependency Status

`artifacts/NTPE_S7_15_EXTERNAL_RESOURCE_DEPENDENCY_STATUS.md`.

| Resource | Status | Available | Blocking |
|----------|--------|-----------|----------|
| Human Evaluators | UNAVAILABLE | NO | **YES** |
| Reference Data | MISSING | NO | **YES** |
| Character Arc | EXTERNAL_DEPENDENCY | NO | Calibration-dependent |
| Pilot Corpus | SPECIFIED | NO | **YES** |
| Candidates | SPECIFIED | NO | **YES** |
| Blinding / Randomization / Provenance | READY | YES | verify at pilot |

Ownership: `OWNER = TBD` (ownership dependency).

## 15. Offline Preflight

`tools/one_shots/s7_15_external_resource_preflight.py` → `overall = PASS`,
failures = none, warnings = [`external_dependencies_not_available`] (expected).

## 16. Attack Tests

`tools/one_shots/s7_15_external_resource_attack_test.py` → 14/14 DETECTED:

| Attack | Result |
|--------|--------|
| Evaluator conflict (`creator==evaluator`) | FAIL (detected) |
| Missing provenance | FAIL (detected) |
| Fake GOLD (machine, unvalidated) | FAIL (detected) |
| Character-arc missing | WARN (detected) |
| Duplicate source | FAIL (detected) |
| Endpoint ambiguity | FAIL (detected) |
| Version mismatch | FAIL (detected) |

## 17. Pilot Entry Conditions

Human Evaluators = ACCEPTED · Reference = ACCEPTED (or reference-free declared) ·
Corpus = ACCEPTED · Candidates = ACCEPTED · Blinding = VERIFIED · Randomization = VERIFIED ·
Provenance = VERIFIED · R1 = CLOSED · R3 = CLOSED · H02 resolved or explicitly accepted as
non-blocking for pilot. Then a separate `S7-16`-style pilot task may start (task ID per
repository governance).

## 18. Calibration Entry Conditions

Pilot executed · Pilot GO · reference corpus sufficient · human reliability sufficient ·
R1/R2/R3 closed · H02 calibration dependency resolved · pre-registration frozen · holdout
protected. S7-15 claims none of these currently hold.

## 19. Remaining External Dependencies

- **A** Real human evaluators — UNAVAILABLE.
- **B** Trusted reference data (GOLD/SILVER/BRONZE) — MISSING.
- **C** Character-arc annotation — EXTERNAL_DEPENDENCY.
- Plus corpus manifest and approved candidate bundles not yet populated.

These are external resource/data/annotation dependencies, not code defects.

## 20. Production Boundary Verification

| Boundary | Evidence | Status |
|----------|----------|--------|
| Model | `meta/llama-3.2-90b-vision-instruct` | FROZEN |
| Provider | `nvidia` | FROZEN |
| Retry | `adaptive_retry_policy.py` (max 5, switch after 3, chunk halving) | PRESERVED |
| Context | `quality_context_scene_v72=false` | FROZEN OFF |
| PS-03 / 80/65 | `ntpe_literary_evaluation.py` | UNCHANGED |
| Production files modified by S7-15 | none | NO |

## 21. Regression Tests

```text
Before: 37/37 PASS
After:  37/37 PASS
```

## 22. Human Evaluation
```text
0
```
## 23. Pilot
```text
0
```
## 24. Calibration
```text
0
```
## 25. Real Translation
```text
0
```
## 26. Provider / Network
```text
0
```
## 27. Production Code Modified
```text
NO
```
## 28. Root Hygiene
```text
PASS
```
## 29. Final Verdict

```text
S7_15_EXTERNAL_RESOURCE_ACQUISITION_SPECIFICATION_COMPLETE_RESOURCES_NOT_AVAILABLE
```

### Decision Split

```text
Specification Readiness:  READY
Acquisition Readiness:    READY_TO_ACCEPT_EXTERNAL_RESOURCES
Pilot Operational Readiness: BLOCKED_BY_EXTERNAL_DEPENDENCIES
Calibration:              NOT AUTHORIZED
Production Literary Quality: OBSERVATIONAL_ONLY
```

`READY_TO_ACCEPT_EXTERNAL_RESOURCES` means NTPE now knows what resources may enter — not
that they exist.

### Required Final Status Table

| Dependency | Specification | Acquisition Mechanism | Validation | Current Availability | Blocking |
|------------|---------------|-----------------------|------------|----------------------|----------|
| Human Evaluators | PASS | roster + qualification gate | qualification/conflict | UNAVAILABLE | YES |
| Reference Data | PASS | submission + review | provenance/review/completeness | MISSING | YES |
| Character Arc | PASS | annotation + adjudication | schema/provenance | EXTERNAL_DEPENDENCY | Calibration-dependent |
| Pilot Corpus | PASS | manifest + stratification audit | offline validation | NOT POPULATED | YES |
| Candidates | PASS | approved offline bundles | provenance | NOT POPULATED | YES |

### Compliance Block

```text
Model: meta/llama-3.2-90b-vision-instruct
Provider: nvidia
Production Quality: OBSERVATIONAL_ONLY
PS-03: UNCHANGED
80/65: UNCHANGED
Retry: PRESERVED
Context: quality_context_scene_v72=false
Human Evaluation: 0
Human Labels: 0
Reference Created: 0
Character Arc Annotation Collected: 0
Pilot: 0
Calibration: 0
Real Translation: 0
Provider / Network: 0
Production Code Modified: NO
Regression: 37/37 PASS
Root Hygiene: PASS
Commit: NO
Push: NO
Tag: NO
```

---

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Acquisition Report | `artifacts/NTPE_S7_15_EXTERNAL_RESOURCE_ACQUISITION_REPORT.md` |
| Human Evaluator Spec | `artifacts/NTPE_S7_15_HUMAN_EVALUATOR_ACQUISITION_SPEC.md` |
| Reference Spec | `artifacts/NTPE_S7_15_REFERENCE_ACQUISITION_SPEC.md` |
| Character-Arc Spec | `artifacts/NTPE_S7_15_CHARACTER_ARC_ANNOTATION_SPEC.md` |
| Pilot Corpus Spec | `artifacts/NTPE_S7_15_PILOT_CORPUS_ACQUISITION_SPEC.md` |
| Candidate Spec | `artifacts/NTPE_S7_15_CANDIDATE_OUTPUT_ACQUISITION_SPEC.md` |
| External Intake Spec | `artifacts/NTPE_S7_15_EXTERNAL_DATA_INTAKE_SPEC.md` |
| Pilot Manifest Schema | `artifacts/s7_15_pilot/PILOT_MANIFEST_SCHEMA.md` |
| Dependency Status | `artifacts/NTPE_S7_15_EXTERNAL_RESOURCE_DEPENDENCY_STATUS.md` |
| Evaluator Package | `artifacts/s7_15_evaluator/{EVALUATOR_INSTRUCTIONS,TRAINING_PROTOCOL,PRACTICE_PROTOCOL,BLINDING_RULES,CONFLICT_RULES,WITHDRAWAL_RULES}.md` |
| Preflight Tool | `tools/one_shots/s7_15_external_resource_preflight.py` |
| Attack Test | `tools/one_shots/s7_15_external_resource_attack_test.py` |

**Commit: NO · Push: NO · Tag: NO**

---

*End of S7-15 Report*
