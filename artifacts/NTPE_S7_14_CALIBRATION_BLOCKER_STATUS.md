# NTPE S7-14 Calibration Blocker Status

**As of**: 2026-09-30

| Blocker | Status Before | S7-14 Result | Calibration Blocking |
|---------|---------------|--------------|----------------------|
| R1 Nested CV / validation overlap | OPEN | `CLOSED_VERIFIED` (Split & Nested CV Policy) | No (closed) |
| R2 Primary endpoint "ρ or AUC" | OPEN | `CLOSED_VERIFIED` (Primary = aggregate Spearman ρ) | No (closed) |
| R3 Missing / outlier rules | OPEN | `CLOSED_VERIFIED` (Missing Data & Outlier Policy) | No (closed) |
| H02 Character-arc grouping | PARTIAL | `EXTERNAL_DEPENDENCY` (arc annotation needed) | Calibration split requirement unresolved |

## Notes

- R1/R2/R3 are closed at the **methodology** level, by explicit policy artifacts. This
  does **not** authorize calibration execution.
- H02 remains an external annotation dependency; it does not block the pilot but leaves
  the calibration split requirement unresolved until arcs exist.
- Even with all four resolved, calibration cannot execute without real evaluators and
  reference data (Blockers A and B).

## Calibration Authorization

```text
NOT AUTHORIZED
```
