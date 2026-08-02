import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

with open(os.path.join(base_path, "RM_5_7_2A_SCENE_PROMPT.md"), "a", encoding="utf-8") as f:
    f.write("""

---

## 5. Failure Handling

| Failure Mode | Detection | Response |
|--------------|-----------|----------|
| No scene boundaries found | Empty extraction result | Return empty array [] |
| Schema validation failure | JSON Schema validation | Return error object with error_code: SCHEMA_VIOLATION |
| Confidence below threshold | confidence < 0.3 | Include but flag with review_status: needs_review |
| Ambiguous boundary | Overlapping/uncertain transitions | Extract each candidate boundary separately |
| Missing required field | Required field absent | Return error object with error_code: MISSING_FIELD |

Error Object Format:
```json
{
  "error": true,
  "error_code": "<CODE>",
  "message": "<description>",
  "source_location": "<location>",
  "partial_results": []
}
```

---

## 6. Confidence Rules

| Evidence Level | Confidence Range | Criteria |
|----------------|------------------|----------|
| Explicit boundary marker + location + time + participants | 0.9 - 1.0 | Full direct evidence |
| Explicit boundary + location + participants | 0.7 - 0.89 | Strong evidence |
| Explicit boundary + participants only | 0.5 - 0.69 | Moderate evidence |
| Boundary inferred from paragraph break only | 0.3 - 0.49 | Weak evidence |
| Ambiguous/uncertain | 0.0 - 0.29 | Flag for review |

**Confidence Calculation**:
- Start at 0.4 for paragraph/chapter break
- +0.3 for explicit transition phrase ("later that day", "meanwhile", etc.)
- +0.2 for explicit location statement
- +0.1 for explicit time marker
- +0.1 per explicit participant mention
- -0.3 for inferred boundary only
- Clamp to [0.0, 1.0]

---

## 7. Duplicate Rules

| Rule ID | Rule | Action |
|---------|------|--------|
| SC-DUP-01 | Same scene_id + same source_location | Merge into single entity |
| SC-DUP-02 | Adjacent segments with same location + participants | Merge; update chapter_range |
| SC-DUP-03 | Overlapping source_location ranges | Keep higher confidence; discard lower |
| SC-DUP-04 | entity_id collision (deterministic hash) | Append sequence suffix |

**Merge Strategy**:
- Keep highest confidence
- Union of participants (by character_id)
- Union of unresolved_references
- Expanded chapter_range
- Most specific boundary_type

---

## 8. Determinism Guarantees

- Temperature = 0 (conceptual)
- No random seeds
- Fixed prompt template
- Deterministic UUID generation: uuidv5(namespace, source_location + "|" + scene_id)
- Fixed field ordering in JSON output (alphabetical keys)
- No timestamp variance (use fixed extraction_timestamp for reproducibility)

---

## 9. Schema Compliance Checklist

- [ ] All required fields present
- [ ] entity_type = scene (const)
- [ ] schema_version = 1.0
- [ ] scene_id pattern ^SC-\d+$
- [ ] time_of_day in enum
- [ ] tone in enum
- [ ] boundary_type in enum
- [ ] confidence in [0.0, 1.0]
- [ ] created_at, updated_at ISO8601
- [ ] version >= 1
- [ ] additionalProperties = false respected
- [ ] UUIDv4 format for entity_id
- [ ] No extra fields beyond schema

---

*End of Scene Extractor Prompt Design*
""")

print("Scene Part 2 complete")