# NTPE S7-14 Reference Data Requirements

**Dependency class**: `REFERENCE_DATA` — `EXTERNAL_DATA_DEPENDENCY`
**Current status**: `MISSING_EXTERNAL_DEPENDENCY` (no GOLD/SILVER/BRONZE references exist)

S7-14 creates **zero** new reference translations. Machine outputs are never presented
as human references.

---

## 1. Reference Classes (unchanged from S7-09 §10 / v1.1 §18)

| Class | Creator | Review | Calibration | Validation | Holdout |
|-------|---------|--------|-------------|------------|---------|
| GOLD | Professional translator | ≥2 reviews + adjudication | ✅ | ✅ | ✅ |
| SILVER | Human-edited MT | 1 review + approval | ⚠️ limited | ⚠️ limited | ❌ |
| BRONZE | Single human | None | Diagnostic only | ❌ | ❌ |

## 2. Required per-reference fields

`reference_id`, `source_id`, `reference_text`, `reference_class`, `creator_id`,
`reviewer_ids[]`, `approval_date`, `revision_count`, `terminology_policy`,
`provenance`.

## 3. Eligibility rules

- GOLD required for holdout-anchored evaluation.
- SILVER may support calibration with caveat; not holdout.
- BRONZE diagnostic only; cannot be a gold calibration target without re-validation.
- Machine output / developer fixture / synthetic → **not** eligible as reference.

## 4. Role Separation

`reference_creator ≠ evaluator` for the same evidence unit; enforced via metadata.

## 5. Current Gap

No GOLD/SILVER/BRONZE reference translation exists in the repository — only Korean
sources (`original_ko.txt`) and machine outputs (`original_ko_zh.txt`). This is an
**external data dependency**, not a code defect.

## 6. Required Action (external, separate task)

Produce at minimum one approved GOLD reference set, or explicitly run a reference-free
rubric pilot (which cannot support reference-anchored calibration).
