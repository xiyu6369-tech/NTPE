# NTPE S7-14 Missing Data and Outlier Policy

**Closes**: S7-12 R3 (Missing-data / outlier rules not fully enumerated)
**Status**: `R3 = CLOSED_VERIFIED`
**Supersedes**: Calibration Design v1.1 §17 (which asserted "predefined" rules without enumerating them)

All rules are **predefined, auditable, and outcome-independent** (frozen before data
collection). No result-dependent deletion is permitted.

---

## 1. Missing Data Taxonomy

| Code | Meaning |
|------|---------|
| `MISSING` | Item not answered / no response recorded |
| `ABSTAIN` | Evaluator explicitly chose "cannot judge" |
| `INVALID` | Response violates protocol (e.g., out-of-range, malformed) |
| `INATTENTIVE` | Failed a pre-registered attention check |
| `DUPLICATE` | Same evaluator/item submitted more than once |
| `SYSTEM_FAILURE` | Technical failure prevented response capture |
| `PROTOCOL_VIOLATION` | Response violates a pre-registered protocol rule |

No further categories may be added post-hoc; new needs are recorded as `PROPOSED_NEW_CODE`.

## 2. Missing Handling (per code)

| Code | Counted as rating? | Retained in raw? | Excluded from analysis? | Imputed? | Reported? |
|------|--------------------|------------------|--------------------------|----------|-----------|
| MISSING | No | Yes | Yes (pairwise complete-case; coverage reported) | No | Yes |
| ABSTAIN | No | Yes | Yes (reported separately) | No | Yes |
| INVALID | No | Yes | Yes | No | Yes |
| INATTENTIVE | No | Yes | Yes; evaluator's other items flagged | No | Yes |
| DUPLICATE | Keep first by timestamp | Yes | Later duplicates excluded | No | Yes |
| SYSTEM_FAILURE | No | Yes | Yes | No | Yes |
| PROTOCOL_VIOLATION | Per rule | Yes | Per rule (predefined) | No | Yes |

Forbidden everywhere: silent deletion, zero-fill, mean-fill, post-hoc fill.

## 3. Abstention Handling

- Retained as its own category; reported as a rate.
- Analysed with and without abstentions in sensitivity analysis.
- Never converted to a numeric score.

## 4. Invalid Evaluation

- Excluded from primary reliability but retained in raw.
- Evaluator-level: if the pre-registered invalidity threshold is exceeded, the evaluator's affected items are flagged (never silently dropped for "ugly" scores).

## 5. Duplicate Handling

- Deterministic: retain earliest by timestamp, exclude later duplicates.
- Duplicate candidate/sample assignment is detected at preflight and blocks the affected assignment.

## 6. Outlier Definition

Distinguish four, non-interchangeable, classes:

| Class | Definition | Handling |
|-------|------------|----------|
| Statistical outlier | Extreme numeric value under a pre-registered rule | Reported; sensitivity analysis; not auto-deleted |
| Protocol-invalid observation | Violates a pre-registered protocol rule | Excluded per rule; logged |
| Evaluator-quality issue | Systematic disagreement under a pre-registered criterion | Flagged; exclusion only if criterion predefined |
| Data corruption | Detected integrity failure | Excluded; logged; source investigated |

A **low score is NOT an outlier**. A **low-agreement evaluator is NOT automatically excluded**.

## 7. Exclusion Criteria (predefined only)

- Any exclusion must cite a pre-registered rule and an outcome-independent trigger.
- Exclusions are logged with `evaluator_id`, `rule_triggered`, `timestamp`, `evidence`.
- Exclusion decisions are made blind to the study's desired conclusion.

## 8. Sensitivity Analysis

- Primary analysis + sensitivity analysis (with/without flagged items) both reported.
- Divergence between the two is reported, not hidden.

## 9. Reporting Requirement

- Report counts per code, per dimension, and per evaluator.
- Report all exclusions and their rule citations.
- Never remove inconvenient observations to improve agreement.

---

## 10. Final Status

| Item | Result |
|------|--------|
| All exclusion rules predefined | YES |
| Result-dependent deletion | FORBIDDEN |
| R3 | `CLOSED_VERIFIED` |
