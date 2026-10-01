# NTPE S7-14 Human Evaluator Requirements

**Dependency class**: `HUMAN_EVALUATOR` — `EXTERNAL_RESOURCE_DEPENDENCY`
**Current status**: `UNAVAILABLE` (0 real evaluators)

S7-14 defines requirements only. It does **not** recruit, contact, or collect personal
data, and it does **not** fabricate evaluators.

---

## 1. Definition of a Valid Evaluator

A **real human** who is not an LLM, agent, mock, or developer self-rating. LLM/agent
"evaluators" and developer self-scoring are explicitly prohibited.

## 2. Evaluator Count Target

- Target: **3–5** evaluators.
- This is a **pilot design target, not a validated requirement**.
- If fewer than 3: reliability analysis is limited; results must not be presented as
  formal reliability evidence.

## 3. Qualification (from S7-09 §12.1 / v1.1)

| Criterion | Proposed minimum |
|-----------|------------------|
| Language | Native Traditional Chinese speaker |
| Literary exposure | ≥50 Korean novels read in translation |
| Translation experience | ≥2 years KO→ZH-TW or equivalent editing |
| Blind test | ≥80% agreement with gold on calibration set (pre-registered) |

## 4. Training / Practice

- Orientation: read rubric, review annotated examples.
- Practice items are **disjoint** from all evaluation/holdout items.
- Training, practice, evaluation, holdout sets are mutually exclusive.

## 5. Blindness

Evaluators must not see: model, provider, attempt number, production designation,
reference class, prompt version, condition identity, PS-03 scores (see
`artifacts/s7_14_pilot/BLINDING_REQUIREMENTS.md`).

## 6. Randomization & Assignment

- Passage order, A/B order, evaluator assignment randomized / counterbalanced.
- Avoid one evaluator seeing all samples; record assignment design and imbalance
  (see `artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md`).

## 7. Pseudonymous ID

- Store only a pseudonymous `evaluator_id`.
- No name/email/phone/address unless governance explicitly requires it elsewhere.

## 8. Conflict of Interest / Role Separation

- A reference creator must not evaluate the same evidence unit.
- Candidate editors/generators must not evaluate their own candidate.
- Enforced via `creator_id` vs `evaluator_id` disjointness.

## 9. Exclusion Rules

- Only pre-registered invalidity criteria may exclude an evaluator (see
  S7-14 Missing Data & Outlier Policy). No exclusion for "unfavorable scores".

## 10. Session Procedure / Fatigue Control

- Session length, breaks, and items/session are `TBD from pilot` (v1.1 §20) —
  S7-14 does **not** invent fixed minutes.
- Fatigue and carry-over are logged.

## 11. Withdrawal / Abstention

- Evaluators may abort/abstain at any time; abstention retained as a raw category.

---

## 12. Recruitment Boundary

S7-14: recruit 0, contact 0, collect 0 personal data. Requirements only.
