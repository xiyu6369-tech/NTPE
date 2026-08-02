# RM-5.7.2A Extractor Prompt Design Report

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


### 4.3 Scene Schema (scene_schema.json)

| Schema Field | Prompt Coverage | Notes |
|--------------|-----------------|-------|
| entity_id | UUIDv5 deterministic | Check |
| entity_type | Const "scene" | Check |
| schema_version | "1.0" | Check |
| name | = scene_id (SC-NNN) | Check |
| attributes.scene_id | Pattern ^SC-\d+$ | Check |
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


## 6. Validation Readiness (RM-5.7.3)

### 6.1 Schema Validation
- All prompts specify output matching JSON Schema Draft 2020-12
- Required fields explicitly listed
- Enum values match schema exactly
- Type constraints documented

### 6.2 Business Rule Alignment

| Schema Business Rule | Prompt Enforcement |
|---------------------|-------------------|
| CH-001: name unique per project | Duplicate Rules CH-DUP-01/02 |
| CH-002: relationship target exists | Deferred to validation phase |
| CH-003: no self-referential | Not extracted (single segment) |
| CH-004: aliases unique per (char, lang, type) | Duplicate Rules CH-DUP-03 |
| CH-005: cultivation_realm for xianxia | Extraction Rule CH-EXT-08 |
| GL-001: canonical unique per (source, domain) | Duplicate Rules GL-DUP-01/02 |
| GL-002: no alias duplicates canonical | Extraction Rule GL-EXT-08 |
| GL-003: context_rule priority unique | Not applicable at extraction |
| GL-004: forbidden != canonical | Extraction Rule GL-EXT-07 |
| GL-005: confidence >= 0.7 for approved | Confidence Rules + review_status |

### 6.3 Manifest Integration
- Each extraction produces entities ready for manifest inclusion
- entity_count verifiable from output array length
- SHA-256 computable from deterministic JSON output
- validation_summary.schema_valid = true by construction

---

## 7. Testing Recommendations

### 7.1 Unit Tests (Per Extractor)
1. Schema validation - Output passes jsonschema.validate()
2. Determinism - Identical input produces identical output (100 runs)
3. Confidence bounds - All scores in [0.0, 1.0]
4. Required fields - No missing required fields
5. Enum compliance - All enum fields use valid values
6. Duplicate handling - Known duplicates produce merged output

### 7.2 Integration Tests
1. Cross-extractor consistency - Same source_location format
2. Manifest generation - Entities pack into manifest correctly
3. Validation pipeline - RM-5.7.3 validator accepts outputs
4. Round-trip - Extract -> Validate -> Manifest -> Load

### 7.3 Edge Case Tests
1. Empty extraction - Returns [] not null
2. Ambiguous input - Produces flagged entities (confidence < 0.3)
3. Schema boundary - Max length strings, max array sizes
4. Unicode handling - CJK, emoji, special characters preserved

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Provider non-determinism | Medium | High | Zero temperature, fixed seeds, validation |
| Schema drift | Low | High | CI validation on every change |
| Confidence miscalibration | Medium | Medium | Calibration dataset, periodic review |
| Duplicate false positives | Low | Medium | Conservative merge rules, defer cross-chapter |
| Missing extraction | Medium | Low | Low confidence threshold, review flag |

---

## 9. Maintenance Notes

### 9.1 Versioning
- Prompt version tracked in document header
- Schema version in schema_version field
- Breaking changes require MAJOR version bump

### 9.2 Update Procedure
1. Modify prompt document
2. Update corresponding schema if needed
3. Run full validation suite
4. Update this report
5. Tag release

### 9.3 Deprecation Policy
- Old prompt versions archived in docs/governance/rm5/archive/
- Minimum 2 version overlap during transition
- Migration scripts for entity format changes

---

## 10. Compliance Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Deterministic | Check | Fixed templates, UUIDv5, alphabetical keys |
| Provider-independent | Check | No provider-specific syntax |
| Schema-aware | Check | Field-by-field mapping tables |
| RM-5.7.2 schema compatible | Check | Verified against all 5 schemas |
| RM-5.7.3 ready | Check | Business rules aligned, manifest-ready |
| No runtime changes | Check | Documentation only |
| No provider execution | Check | Design phase only |
| No network requests | Check | Design phase only |
| Production code modified = 0 | Check | Only docs created |
| git diff --check PASS | Pending | Requires validation |

---

## 11. Sign-Off

**Design Author**: NTPE AI Workspace  
**Review Date**: 2026-08-02  
**Next Review**: Upon RM-5.7.3 integration testing

### Acceptance Criteria Met
- [x] 5 extractor prompt documents created
- [x] Each contains all 7 required sections
- [x] All prompts schema-compliant
- [x] Determinism guarantees documented
- [x] Cross-extractor consistency verified
- [x] Validation readiness confirmed
- [x] Report document created

---

*End of RM-5.7.2A Prompt Design Report*
