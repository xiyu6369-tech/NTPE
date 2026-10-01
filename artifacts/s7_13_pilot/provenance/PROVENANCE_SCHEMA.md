# S7-13 Pilot Provenance Schema (required, unpopulated)

Every evaluation record must be traceable by the following fields. No records exist
yet because the pilot was not executed.

| Field | Purpose |
|-------|---------|
| `evaluation_id` | unique evaluation row id |
| `sample_id` | pilot sample identifier |
| `source_id` | source passage id |
| `candidate_id` | candidate translation id |
| `reference_id` | reference id (nullable; none exist) |
| `evaluator_id` | pseudonymous evaluator id |
| `evaluation_protocol_version` | protocol version |
| `rubric_version` | rubric version |
| `presentation_order` | order shown |
| `timestamp` | submission timestamp |
| `response` | ok / missing / abstain / invalid |
| `label_conflict` | binary vs Likert conflict flag |

Role-separation fields (v1.1 §16): `reference_creator_id`, `reviewer_ids[]`,
`candidate_selector_independent_of_ps03`.

Privacy: only pseudonymous ids; no name/email/phone/address.
