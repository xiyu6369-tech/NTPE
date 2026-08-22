import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

report_part2b = """

### 4.3 Scene Schema (scene_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "scene" | Check |
| schema_version | "1.0" | Check |
| name | = scene_id (SC-NNN) | Check |
| attributes.scene_id | Pattern ^SC-\\d+$ | Check |
| attributes.title | Always null | Check |
| attributes.volume/chapter_range | From source_location | Check |
| attributes.location | Explicit only | Check |
| attributes.time_of_day | Enum (8 values) | Check |
| attributes.participants | character_id, status, role | Check |
| attributes.plot_points | Empty array | Check |
| attributes.summary | Always null | Check |
| attributes.tone | Enum (9 values) | Check |
| attributes.unresolved_references | Evidence required | Check |
| attributes.boundary_type | Enum (6 values) | Check |
| (all base fields) | Covered | Check |

### 4.4 Narrative Schema (narrative_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "narrative" | Check |
| schema_version | "1.0" | Check |
| name | PP-NNN/TL-NNN/WR-NNN/CM-NNN | Check |
| attributes.narrative_type | Enum (4 values) | Check |
| attributes.plot_point | Conditional object | Check |
| attributes.timeline | Conditional object | Check |
| attributes.world_rule | Conditional object | Check |
| attributes.character_milestone | Conditional object | Check |
| (all base fields) | Covered | Check |

### 4.5 Style Schema (style_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "style" | Check |
| schema_version | "1.0" | Check |
| name | Style identifier | Check |
| attributes.style_type | Enum (7 values) | Check |
| attributes.category | Enum (8 values) | Check |
| attributes.description | Objective | Check |
| attributes.examples | Min 1, max 5 | Check |
| attributes.rules | Derived object | Check |
| attributes.applies_to | Enum (6 values) | Check |
| attributes.priority | 0-100 computed | Check |
| attributes.*_profile | Conditional objects | Check |
| attributes.*_patterns | Array objects | Check |
| (all base fields) | Covered | Check |

---

## 5. Cross-Extractor Consistency

### 5.1 Shared Conventions

| Convention | Implementation |
|------------|----------------|
| UUID Generation | uuidv5(NAMESPACE_DNS, source_location + "|" + primary_key) |
| Timestamp Format | ISO8601 UTC (fixed for determinism) |
| Confidence Range | 0.0 - 1.0 (float) |
| Source Location | volume:chapter:position or file:line-range |
| Error Format | {error: true, error_code, message, source_location, partial_results} |
| Review Status | pending / needs_review / approved / rejected |
| Field Ordering | Alphabetical keys in JSON output |

### 5.2 Confidence Calibration

All extractors use additive confidence calculation with:
- **Base score** for minimal evidence
- **Positive increments** for each additional evidence type
- **Negative increments** for ambiguity/indirectness
- **Clamping** to [0.0, 1.0]

Base scores differ by extractor based on typical evidence density:
- Character: 0.5 (names are usually explicit)
- Glossary: 0.5 (terms are usually explicit)
- Scene: 0.4 (boundaries can be subtle)
- Narrative: 0.4 (events can be implied)
- Style: 0.3 (patterns require recurrence)

### 5.3 Duplicate Handling Strategy

All extractors follow a three-tier merge strategy:
1. **Exact match** (same key + same location) - Full merge
2. **Adjacent match** (same key + adjacent location) - Merge with range expansion
3. **Cross-chapter** (same key + different chapter) - Separate entities, link later
"""

with open(os.path.join(base_path, "RM_5_7_2A_PROMPT_DESIGN_REPORT.md"), "a", encoding="utf-8") as f:
    f.write(report_part2b)

print("Report Part 2b appended")