# NTPE S7-14 Primary Endpoint Policy

**Closes**: S7-12 R2 (Primary endpoint stated as "ρ or AUC" — cherry-picking risk)
**Status**: `R2 = CLOSED_VERIFIED`
**Supersedes**: Calibration Design v1.1 §7.2 ("Aggregate Spearman ρ (or AUC)")

The single primary endpoint is fixed here by **study objective and data type** —
not by which value later looks better.

---

## 1. Primary Endpoint

**Aggregate Spearman ρ** — the rank association between the PS-03 aggregate score
(and any future candidate aggregate) and the human **aggregate ordinal** rating.

Exactly **one** primary endpoint. The disjunction "ρ or AUC" is removed.

## 2. Definition

For each evidence unit, compute PS-03 aggregate and the human aggregate rating
(7-point ordinal or ordinal-safe aggregate). Primary endpoint = Spearman ρ across units.

## 3. Why Selected (methodology evidence, not results)

1. Human label type is **ordinal** (v1.1 §9.1), so the ordinal-appropriate association
   method is primary (v1.1 §9.2, §27).
2. The core study objective is whether the metric **ranks** translation quality
   consistently with human judgment (v1.1 §5 objectives; §12.1 dimension calibration).
3. v1.1 §12.1 already states "Spearman ρ (**primary**)" and §7.2 lists aggregate
   Spearman ρ first.
4. AUC requires a **binary** ACCEPT/REJECT reference and a chosen threshold; the threshold
   is itself `FROZEN / UNCALIBRATED` (v1.1 §14.1). Making AUC primary would couple the
   primary endpoint to an uncalibrated threshold. AUC is therefore a **classification**
   endpoint, not the alignment endpoint.

This selection is independent of observed data.

## 4. Secondary Endpoints

- **AUC** (binary ACCEPT/REJECT discrimination) — classification endpoint.
- **ECE** (≤0.05 target) — calibration of probability outputs.
- **Per-dimension Spearman ρ** (≥0.50 target) — dimension-level alignment.

Secondary endpoints support the primary; they **cannot substitute** for it.

## 5. Exploratory Metrics

- Pearson r (`ASSUMPTION-DEPENDENT`, exploratory only).
- Kendall τ.
- Subgroup analyses (dialogue/narration/scene type).
- Alternate weights, alternate thresholds, win rates.

All exploratory metrics are labelled `EXPLORATORY` and cannot automatically promote.

## 6. Prohibited Endpoint Switching

- Selecting ρ vs AUC after seeing results is FORBIDDEN.
- Reporting only a secondary metric as if primary is FORBIDDEN.
- Dropping the primary because a secondary looks better is FORBIDDEN.

## 7. Pre-Registration Requirement

Primary endpoint, secondary endpoints, and exploratory metrics must be frozen **before**
data collection / calibration.

## 8. Holdout Rule

The primary endpoint is evaluated **once** on the protected holdout (see S7-14
Calibration Split & Nested CV Policy).

---

## 9. Final Status

| Item | Result |
|------|--------|
| Primary endpoint | Aggregate Spearman ρ (ONE) |
| Secondary | AUC, ECE, per-dimension ρ |
| Exploratory | Pearson r, Kendall τ, subgroups, alternates |
| Post-hoc endpoint switching | FORBIDDEN |
| R2 | `CLOSED_VERIFIED` |
