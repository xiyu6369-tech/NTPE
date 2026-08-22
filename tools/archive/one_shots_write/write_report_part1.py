import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

# Write report in parts
report_part1 = """# RM-5.7.2A Extractor Prompt Design Report

**Version**: 1.0  
**Status**: Design Complete  
**Date**: 2026-08-02  
**Scope**: Five Knowledge Generation Extractors (Character, Glossary, Scene, Narrative, Style)

---

## 1. Executive Summary

This report documents the deterministic, provider-independent extraction prompt designs for the five Knowledge Generation extractors introduced in RM-5.7.2. All prompts are designed to produce JSON output compliant with the schemas defined in `schemas/knowledge/` and validated against the RM-5.7.3 Validation Engine requirements.

### Deliverables Created

| File | Extractor | Schema Reference | Status |
|------|-----------|------------------|--------|
| `RM_5_7_2A_CHARACTER_PROMPT.md` | Character | `character_schema.json` | Complete |
| `RM_5_7_2A_GLOSSARY_PROMPT.md` | Glossary | `glossary_schema.json` | Complete |
| `RM_5_7_2A_SCENE_PROMPT.md` | Scene | `scene_schema.json` | Complete |
| `RM_5_7_2A_NARRATIVE_PROMPT.md` | Narrative | `narrative_schema.json` | Complete |
| `RM_5_7_2A_STYLE_PROMPT.md` | Style | `style_schema.json` | Complete |

---

## 2. Design Principles Applied

### 2.1 Determinism
- **Fixed prompt templates** with no variable components beyond explicit placeholders
- **Zero temperature** (conceptual) - no randomness in output generation
- **Deterministic UUID generation** using uuidv5(namespace, source_location + "|" + key_field)
- **Alphabetical key ordering** in JSON output
- **Fixed timestamps** for reproducibility

### 2.2 Provider Independence
- No model-specific tokens, formatting, or instructions
- Standard JSON Schema terminology only
- No provider-specific function calling or tool use syntax
- Compatible with any LLM supporting JSON mode / structured output

### 2.3 Schema Compliance
Each prompt's Output Requirements section maps 1:1 to the corresponding JSON Schema:
- All required fields explicitly specified
- Enum constraints documented
- Type constraints documented
- additionalProperties: false respected

### 2.4 Evidence-Based Extraction
- **Hard constraint**: Only extract what is explicitly in source text
- **No hallucination**: Prohibited from inferring beyond evidence
- **No external knowledge**: No dictionary lookups, no genre tropes
- **Confidence scoring**: Tied to evidence strength

---

## 3. Prompt Architecture Comparison

### 3.1 Common Structure (All 5 Extractors)

```
1. System Prompt          - Role definition, principles, scope, prohibitions
2. User Prompt Template   - Input format, context, instructions, output format
3. Extraction Rules       - Per-field rules with enforcement levels
4. Output Requirements    - Field-by-field schema mapping table
5. Failure Handling       - Error modes, detection, response formats
6. Confidence Rules       - Evidence levels, calculation formula
7. Duplicate Rules        - Deduplication logic, merge strategies
8. Determinism Guarantees - Technical measures for reproducibility
9. Schema Compliance      - Validation checklist
```

### 3.2 Extractor-Specific Variations

| Aspect | Character | Glossary | Scene | Narrative | Style |
|--------|-----------|----------|-------|-----------|-------|
| Primary Key | canonical_name | source_term | scene_id | narrative_type + ID | style_type + pattern |
| Categories | role (6 values) | domain (6 values) | boundary_type (6) | narrative_type (4) | style_type (7) + category (8) |
| Relationships | character<->character | term<->term (syn/ant) | scene<->plot_point | plot<->plot, char<->milestone | pattern<->translation |
| Confidence Base | 0.5 (name mention) | 0.5 (term mention) | 0.4 (boundary) | 0.4 (event mention) | 0.3 (pattern) |
| Duplicate Key | canonical_name + location | source_term + location | scene_id + location | element_id + location | pattern + type + category |
"""

with open(os.path.join(base_path, "RM_5_7_2A_PROMPT_DESIGN_REPORT.md"), "w", encoding="utf-8") as f:
    f.write(report_part1)

print("Report Part 1 written")