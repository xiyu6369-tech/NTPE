# NTPE S7-14 Provenance Requirements

**Dependency class**: `PROVENANCE`
**Current status**: READY (schema defined; no records yet)

---

## 1. Required Provenance Fields (per evaluation record)

`evaluation_id`, `sample_id`, `source_id`, `candidate_id`, `reference_id`,
`evaluator_id` (pseudonymous), `evaluation_protocol_version`, `rubric_version`,
`presentation_order`, `timestamp`, `response` (ok/missing/abstain/invalid),
`label_conflict`.

Role-separation fields: `reference_creator_id`, `reviewer_ids[]`,
`candidate_selector_independent_of_ps03`.

## 2. Traceability Chain

```
source → candidate → reference → evaluator → protocol/rubric version → presentation → timestamp
```

## 3. Raw vs Derived (immutability)

- RAW human response: **immutable** once submitted.
- DERIVED analysis tables: regenerable; must never overwrite raw.
- Storage: `artifacts/s7_14_pilot/raw/` (immutable) vs `artifacts/s7_14_pilot/derived/` (regenerable).

## 4. Privacy

- Only pseudonymous `evaluator_id`.
- No name/email/phone/address stored in the repository.
- External/raw personal info handled per project governance outside Git.

## 5. Integrity Checks (preflight)

- raw row count vs expected
- duplicate evaluation ids
- missing required fields
- invalid evaluator ids
- duplicate sample/candidate assignment

## 6. Verification

- `tools/one_shots/s7_14_pilot_readiness.py` checks presence of provenance schema
  fields and raw/derived separation.
