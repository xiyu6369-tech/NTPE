# NTPE S7-14 Calibration Split and Nested CV Policy

**Closes**: S7-12 R1 (Validation-set role overlaps nested-CV inner tuning)
**Status**: `R1 = CLOSED_VERIFIED`
**Supersedes ambiguity in**: Calibration Design v1.1 §12.2, §13.2, §15

This policy defines **one unambiguous four-layer boundary** so that
`inner tuning ≠ outer validation ≠ final holdout`.

---

## 1. Calibration Set (60% of chapters)

- Unit: chapter group (grouped by chapter and author; scenes never split).
- Purpose: **fit / tune / select**. This is the ONLY place model selection happens.

## 2. Inner CV (inside the Calibration Set)

- Grouped by chapter (and author when ≥3 authors).
- Allowed: fit weights, tune λ / hyperparameters, select the candidate-threshold procedure.
- This is where **every tuning decision** is made.

## 3. Outer Validation (20% of chapters)

- Purpose: **evaluate the frozen procedure selected from Calibration + Inner CV** — exactly once per frozen procedure version.
- Allowed: compute performance of the already-selected procedure; decide whether to proceed.
- Forbidden: any tuning, weight selection, metric selection, threshold-method selection, or iterative refinement based on its results.

## 4. Final Holdout (20% of chapters)

- Purpose: **one-time final unbiased evaluation** of the fully frozen procedure.
- Sealed until all design/selection decisions are frozen; evaluated once.
- Forbidden: tuning, selection, inspecting for iterative optimization, or re-running after protocol changes (a changed procedure invalidates the holdout result).

---

## 5. Required Data Flow

```
Calibration Dataset (60%)
        ↓
Outer Fold  (inner CV drives selection)
        ↓
Inner CV
        ↓
Tune / Select          <-- only here
        ↓
Outer Validation (20%) <-- evaluate once, never tune
        ↓
Frozen Procedure
        ↓
Final Holdout (20%)    <-- one-time final
```

Prohibited pattern: `Validation → tuning → validation again`.

---

## 6. Allowed / Forbidden Operations per Layer

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| Calibration + Inner CV | fit, tune, select weights/λ/threshold procedure | touching validation/holdout |
| Outer Validation | evaluate frozen procedure once | tune, re-select, iterate, inspect for optimization |
| Final Holdout | one-time final evaluation | tune, select, repeatedly inspect, re-run after change |

---

## 7. Leakage Rules

- No chapter/scene/author may cross any layer boundary.
- Grouped CV folds; no same candidate or reference across layers.
- Outer Validation is consumed at most once per procedure version.
- Holdout remains sealed until the procedure is frozen.
- Results from Outer Validation must never feed back into fitting.

## 8. Repeated Analysis Rules

- If the procedure changes after Outer Validation inspection, the used validation set is **spent**; reuse requires a fresh validation set or must be labelled exploratory and cannot support confirmatory promotion.

## 9. Final Holdout Protection

- Holdout is evaluated exactly once.
- Any post-hoc change to endpoint, weights, threshold, or exclusion rules invalidates the holdout result as confirmatory evidence.

---

## 10. Final Status

| Item | Result |
|------|--------|
| Inner tuning ≠ Outer validation | ENFORCED |
| Outer validation ≠ Final holdout | ENFORCED |
| R1 | `CLOSED_VERIFIED` |
