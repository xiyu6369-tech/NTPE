import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

# Narrative Part 2
narrative_part2 = """

---

## 3. Extraction Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| NR-EXT-01 | Only extract narrative elements explicitly stated in source text | Hard constraint |
| NR-EXT-02 | narrative_type = classify based on explicit markers in text | Enum constrained |
| NR-EXT-03 | plot_point: only explicit events with clear occurrence | Evidence required |
| NR-EXT-04 | plot_point.type = only if explicitly labeled in source (e.g., \"turning point\") | Enum constrained |
| NR-EXT-05 | timeline: only explicit chronological markers (\"three days later\", \"year 100\") | Evidence required |
| NR-EXT-06 | world_rule: only explicitly stated systems/laws/constraints | Direct evidence |
| NR-EXT-07 | world_rule.category = from explicit context markers | Enum constrained |
| NR-EXT-08 | character_milestone: only explicit breakthroughs/transformations | Evidence required |
| NR-EXT-09 | milestone_type = from explicit descriptors in text | Enum constrained |
| NR-EXT-10 | impact_level = NULL (not extracted at this stage) | Always null |
| NR-EXT-11 | prerequisite/consequence plots = only if explicitly linked in source | Direct evidence |

---

## 4. Output Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| entity_id | string (UUIDv4) | Yes | Unique per extraction |
| entity_type | string | Yes | Const: narrative |
| schema_version | string | Yes | Pattern: ^\\d+\\.\\d+$ |
| name | string | Yes | 1-200 chars, = narrative element ID |
| attributes.narrative_type | string | Yes | Enum: plot_point/timeline/world_rule/character_milestone |
| attributes.plot_point | object | Conditional | Required if narrative_type=plot_point |
| attributes.timeline | object | Conditional | Required if narrative_type=timeline |
| attributes.world_rule | object | Conditional | Required if narrative_type=world_rule |
| attributes.character_milestone | object | Conditional | Required if narrative_type=character_milestone |
| source_text | string | Yes | Exact source segment |
| source_location | string | Yes | Format: vol:ch:pos |
| confidence | number | Yes | 0.0-1.0 |
| metadata | object | Yes | See schema |
| created_at | string | Yes | ISO8601 UTC |
| updated_at | string | Yes | ISO8601 UTC |
| version | integer | Yes | >=1 |
| references | object | Yes | Empty at extraction |
| tags | array[string] | Yes | May be empty |

---

## 5. Failure Handling

| Failure Mode | Detection | Response |
|--------------|-----------|----------|
| No narrative elements found | Empty extraction result | Return empty array [] |
| Schema validation failure | JSON Schema validation | Return error object with error_code: SCHEMA_VIOLATION |
| Confidence below threshold | confidence < 0.3 | Include but flag with review_status: needs_review |
| Ambiguous classification | Element fits multiple types | Extract as primary type; note alternatives in tags |
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
| Explicit event + type + characters + consequences | 0.9 - 1.0 | Full direct evidence |
| Explicit event + type + characters | 0.7 - 0.89 | Strong evidence |
| Explicit event + characters only | 0.5 - 0.69 | Moderate evidence |
| Event implied by context only | 0.3 - 0.49 | Weak evidence |
| Ambiguous/uncertain | 0.0 - 0.29 | Flag for review |

**Confidence Calculation**:
- Start at 0.4 for explicit event/rule mention
- +0.2 for explicit classification markers
- +0.2 for explicit character involvement
- +0.1 for explicit causal links
- +0.1 for explicit chronological marker
- -0.3 for implied/inferred only
- Clamp to [0.0, 1.0]

---

## 7. Duplicate Rules

| Rule ID | Rule | Action |
|---------|------|--------|
| NR-DUP-01 | Same narrative element ID + same source_location | Merge into single entity |
| NR-DUP-02 | Same plot_id/timeline_id/rule_id + adjacent location | Merge; update source_location range |
| NR-DUP-03 | Cross-chapter same narrative element | Separate entities; link via references later |
| NR-DUP-04 | entity_id collision (deterministic hash) | Append sequence suffix |

**Merge Strategy**:
- Keep highest confidence
- Union of affected_characters
- Union of prerequisite/consequence plots
- Union of constraints/exceptions
- Expanded source_location range

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
- [ ] entity_type = narrative (const)
- [ ] schema_version = 1.0
- [ ] narrative_type in enum
- [ ] Conditional attribute objects present per type
- [ ] plot_point.type in enum (if applicable)
- [ ] world_rule.category in enum (if applicable)
- [ ] milestone_type in enum (if applicable)
- [ ] confidence in [0.0, 1.0]
- [ ] created_at, updated_at ISO8601
- [ ] version >= 1
- [ ] additionalProperties = false respected
- [ ] UUIDv4 format for entity_id
- [ ] No extra fields beyond schema

---

*End of Narrative Extractor Prompt Design*
"""

with open(os.path.join(base_path, "RM_5_7_2A_NARRATIVE_PROMPT.md"), "a", encoding="utf-8") as f:
    f.write(narrative_part2)

print("Narrative Part 2 appended")