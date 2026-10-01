# NTPE S7-15 Human Evaluator Acquisition Specification

**Dependency**: `HUMAN_EVALUATOR` — `EXTERNAL_RESOURCE_DEPENDENCY`
**Current status**: `UNAVAILABLE` (Specification = complete; Availability = NO)
**Extends**: `artifacts/NTPE_S7_14_HUMAN_EVALUATOR_REQUIREMENTS.md` (KEEP / EXTEND)

This spec defines **what kind of real human may enter** the NTPE pilot pipeline and how
an evaluator is validated and accepted. S7-15 does **not** recruit, contact, or score.

---

## 1.1 Evaluator Profile

A **real human** traditional-Chinese literary reader/translator. LLM/agent/mock/self-rating
are prohibited.

## 1.2 Minimum Count

- Target 3–5 (pilot design target; **not a validated requirement**).
- <3 → reliability analysis limited; not formal reliability evidence.

## 1.3 Qualification (minimum quality)

| Requirement | Status |
|-------------|--------|
| Real human | MUST |
| Understands evaluation language (zh-TW) | MUST |
| Understands rubric | MUST |
| Distinguishes source meaning from literary quality | MUST |
| Native zh-TW reader | minimum (from S7-09) |
| KO comprehension sufficient to verify fidelity | required for fidelity judgments |
| Literary translation familiarity (≥50 KO novels / ≥2y) | `TBD — validate through pilot qualification` |
| Blind qualification test ≥80% vs gold | `TBD — validated through pilot qualification procedure` |

Do **not** invent "expert" thresholds without empirical basis.

## 1.4 Training / Practice

- Mandatory training + practice before pilot.
- Practice items disjoint from pilot/calibration/holdout.
- Training/Practice/Pilot are mutually exclusive.

## 1.5 Conflict of Interest / Role Separation

Roles: `Reference Creator`, `Evaluator`, `Study Administrator`, `Data Analyst`.
Hard rule: `Reference Creator ≠ Evaluator` for the same evidence unit.
Multi-role = explicit conflict policy required.

## 1.6 Blindness / Session / Fatigue

- Blind to model/provider/attempt/condition/reference-class/prompt/PS-03.
- Session length, break, items/session = `TBD from pilot` (not invented here).
- Fatigue + carry-over logged.

## 1.7 Compensation / Burden Recording

- Record burden (time/task) as metadata; compensation policy = `TBD` (governance).

## 1.8 Privacy

- Only pseudonymous `evaluator_id`.
- No name/email/phone/address in repository artifacts.

## 1.9 Withdrawal / Replacement

- Withdrawal allowed anytime; retained as raw category.
- Replacement allowed only by pre-registered rule; log replacement reason.

## 1.10 Identity

- `evaluator_id` pseudonymous; identity validation gate before acceptance.

## 1.11 Assignment

- Balanced randomized assignment with recorded seed; no unlogged ad-hoc assignment.

## 1.12 Qualification Gate

identity validation → language suitability → instruction comprehension → practice
completion → protocol compliance. Comprehension scores are **qualification evidence**,
never literary-quality evidence.

## 1.13 Exclusion

Only for predefined protocol violation / data corruption / identity issue / COI /
withdrawal. **Never** for low agreement, unfavorable ratings, or unexpected preference.

---

## Acceptance

Evaluator is `ACCEPTED` only when qualified and recorded with a pseudonymous ID and no
conflict. Until then: `MISSING`/`UNAVAILABLE`.
