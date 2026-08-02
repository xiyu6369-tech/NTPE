import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

report_part2a = """

## 4. Schema Alignment Verification

### 4.1 Character Schema (character_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "character" | Check |
| schema_version | "1.0" | Check |
| name | = canonical_name | Check |
| attributes.canonical_name | Extraction Rule CH-EXT-02 | Check |
| attributes.source_name | Extraction Rule CH-EXT-03 | Check |
| attributes.aliases | Extraction Rule CH-EXT-04 | Check |
| attributes.role | Enum constrained (CH-EXT-05) | Check |
| attributes.traits | Evidence required (CH-EXT-06) | Check |
| attributes.relationships | Direct evidence (CH-EXT-07) | Check |
| attributes.cultivation_realm | Genre-conditional (CH-EXT-08) | Check |
| attributes.first_appearance | Optional (CH-EXT-09) | Check |
| attributes.knowledge_tags | Controlled vocab (CH-EXT-10) | Check |
| attributes.arc_summary | Always null (CH-EXT-11) | Check |
| source_text | Exact segment | Check |
| source_location | vol:ch:pos format | Check |
| confidence | 0.0-1.0 with calculation | Check |
| metadata | Full metadata object | Check |
| created_at/updated_at | ISO8601 UTC | Check |
| version | >=1 | Check |
| references | Empty at extraction | Check |
| tags | May be empty | Check |

### 4.2 Glossary Schema (glossary_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "glossary" | Check |
| schema_version | "1.0" | Check |
| name | = source_term | Check |
| attributes.canonical_translation | May be null | Check |
| attributes.source_term | Exact surface form | Check |
| attributes.domain_tags | Controlled vocabulary | Check |
| attributes.part_of_speech | Enum constrained | Check |
| attributes.context_rules | Optional | Check |
| attributes.forbidden_forms | Evidence required | Check |
| attributes.aliases | No invention | Check |
| attributes.notes | Always null | Check |
| attributes.relationships | Direct evidence only | Check |
| (all base fields) | Covered | Check |
"""

with open(os.path.join(base_path, "RM_5_7_2A_PROMPT_DESIGN_REPORT.md"), "a", encoding="utf-8") as f:
    f.write(report_part2a)

print("Report Part 2a appended")