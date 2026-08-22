import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

with open(os.path.join(base_path, "RM_5_7_2A_STYLE_PROMPT.md"), "a", encoding="utf-8") as f:
    f.write("""

---

## 5. Failure Handling

| Failure Mode | Detection | Response |
|--------------|-----------|----------|
| No style patterns found | Empty extraction result | Return empty array [] |
| Schema validation failure | JSON Schema validation | Return error object with error_code: SCHEMA_VIOLATION |
| Confidence below threshold | confidence < 0.3 | Include but flag with review_status: needs_review |
| Insufficient examples | pattern frequency < 3 | Do not extract as collocation_pattern |
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
| High-frequency pattern + approved translation pairs | 0.9 - 1.0 | Full direct evidence |
| Recurring pattern (freq >= 5) + clear examples | 0.7 - 0.89 | Strong evidence |
| Recurring pattern (freq >= 3) + examples | 0.5 - 0.69 | Moderate evidence |
| Single occurrence with clear structure | 0.3 - 0.49 | Weak evidence |
| Ambiguous/uncertain | 0.0 - 0.29 | Flag for review |

**Confidence Calculation**:
- Start at 0.3 for any identifiable pattern
- +0.2 per recurrence above threshold (max +0.4)
- +0.2 for approved translation pair evidence
- +0.1 for cross-chapter consistency
- +0.1 for explicit rule markers
- -0.3 for single occurrence only
- -0.2 for subjective interpretation required
- Clamp to [0.0, 1.0]

---

## 7. Duplicate Rules

| Rule ID | Rule | Action |
|---------|------|--------|
| ST-DUP-01 | Same pattern + same style_type + same category | Merge; combine examples |
| ST-DUP-02 | Same source_pattern + different target (translation_preferences) | Keep highest confidence; note alternatives |
| ST-DUP-03 | Overlapping n-grams in collocation_patterns | Merge longer pattern; sum frequencies |
| ST-DUP-04 | entity_id collision (deterministic hash) | Append sequence suffix |

**Merge Strategy**:
- Keep highest confidence
- Union of examples (max 5)
- Union of rules
- Maximum priority
- Combined frequency for collocations

---

## 8. Determinism Guarantees

- Temperature = 0 (conceptual)
- No random seeds
- Fixed prompt template
- Deterministic UUID generation: uuidv5(namespace, source_location + "|" + name)
- Fixed field ordering in JSON output (alphabetical keys)
- No timestamp variance (use fixed extraction_timestamp for reproducibility)

---

## 9. Schema Compliance Checklist

- [ ] All required fields present
- [ ] entity_type = style (const)
- [ ] schema_version = 1.0
- [ ] style_type in enum (7 values)
- [ ] category in enum (8 values)
- [ ] applies_to in enum (6 values)
- [ ] priority in [0, 100]
- [ ] confidence in [0.0, 1.0]
- [ ] created_at, updated_at ISO8601
- [ ] version >= 1
- [ ] additionalProperties = false respected
- [ ] UUIDv4 format for entity_id
- [ ] No extra fields beyond schema

---

*End of Style Extractor Prompt Design*
""")

print("Style Part 2 complete")