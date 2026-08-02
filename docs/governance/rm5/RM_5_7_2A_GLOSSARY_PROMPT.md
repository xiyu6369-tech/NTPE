# RM-5.7.2A Glossary Extractor Prompt Design

**Version**: 1.0  
**Status**: Design Complete  
**Schema Reference**: schemas/knowledge/glossary_schema.json  
**Compatible With**: RM-5.7.3 Validation Engine

---

## 1. System Prompt

`
You are a deterministic glossary/terminology knowledge extractor for literary translation pipelines. Your task is to extract terminology entities from source text segments and output them as structured JSON compliant with the NTPE Glossary Knowledge Schema (v1.0).

CORE PRINCIPLES:
- Extract ONLY terms explicitly present in the provided source text
- NEVER invent translations, definitions, or domain classifications not supported by evidence
- Output MUST be valid JSON matching the schema exactly
- No markdown, no explanations, no free-form text
- Deterministic output: identical input must produce identical output
- Provider-independent: no model-specific tokens or formatting

EXTRACTION SCOPE:
- terminology (source term + canonical translation suggestion)
- organizations (named groups, sects, clans, companies)
- locations (named places, realms, cities, landmarks)
- techniques (cultivation methods, martial arts, skills)
- items (artifacts, weapons, pills, talismans)
- titles (honorifics, ranks, positions)

EACH TERM MUST INCLUDE:
- source (original term in source language)
- translation suggestion (proposed target language equivalent)
- category (terminology/organization/location/technique/item/title)
- confidence score (0.0-1.0 based on evidence strength)
- evidence (exact source text span supporting extraction)

PROHIBITED:
- Inventing translations for untranslated terms
- Assigning categories not evident from context
- Using external dictionaries or knowledge bases
- Any interpretive gloss or cultural explanation
`

---

## 2. User Prompt Template

`
Extract glossary/terminology entities from the following source text segment.

SOURCE TEXT:
{{source_text}}

SOURCE LOCATION:
{{source_location}}  (format: volume:chapter:position or file:line-range)

CONTEXT:
- Project: {{project_id}}
- Genre: {{genre}}
- Language: {{source_language}}
- Target Language: {{target_language}}
- Existing Glossary: {{known_terms}}  (optional, for consistency)

INSTRUCTIONS:
1. Identify all terms explicitly present in the source text that fall into the six categories
2. For each term, extract only the fields listed in the Output Requirements
3. Assign confidence based on Confidence Rules
4. Apply Duplicate Rules to avoid redundant entries
5. Output as JSON array of glossary entities

OUTPUT FORMAT:
[
  {
    entity_id: <UUIDv4>,
    entity_type: glossary,
    schema_version: 1.0,
    name: <source_term>,
    attributes: {
      canonical_translation: <string>,
      source_term: <string>,
      domain_tags: [<string>, ...],
      part_of_speech: <enum: noun|verb|adjective|adverb|proper_noun|phrase|idiom|other>,
      context_rules: {},
      forbidden_forms: [<string>, ...],
      aliases: [<string>, ...],
      notes: <string|null>,
      relationships: {}
    },
    source_text: <exact_source_segment>,
    source_location: <string>,
    confidence: <float_0_1>,
    metadata: {
      extraction_method: deterministic_prompt_v1,
      extraction_model: <model_identifier>,
      extraction_timestamp: <ISO8601>,
      validator_version: 1.0,
      review_status: pending,
      lock_status: unlocked
    },
    created_at: <ISO8601>,
    updated_at: <ISO8601>,
    version: 1,
    references: {},
    tags: []
  }
]
`


---

## 3. Extraction Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| GL-EXT-01 | Only extract terms explicitly present in source text | Hard constraint |
| GL-EXT-02 | source_term = exact surface form as it appears in source text | Mandatory |
| GL-EXT-03 | canonical_translation = proposed target equivalent; NULL if uncertain | Mandatory (may be null) |
| GL-EXT-04 | category = one of: terminology, organization, location, technique, item, title | Enum constrained |
| GL-EXT-05 | domain_tags = from controlled vocabulary (cultivation, medicine, weapon, etc.) | Controlled vocabulary |
| GL-EXT-06 | part_of_speech = grammatical category of source term | Enum constrained |
| GL-EXT-06 | context_rules = only if source shows context-dependent translation | Optional |
| GL-EXT-07 | forbidden_forms = only translations explicitly marked as wrong in source | Evidence required |
| GL-EXT-08 | aliases = alternative forms explicitly present in source text | No invention |
| GL-EXT-09 | notes = NULL (not extracted at this stage) | Always null |
| GL-EXT-10 | relationships = only explicit semantic links in source (synonym, antonym) | Direct evidence |
| GL-EXT-11 | evidence = exact source text span containing the term | Mandatory |

---

## 4. Output Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| entity_id | string (UUIDv4) | Yes | Unique per extraction |
| entity_type | string | Yes | Const: glossary |
| schema_version | string | Yes | Pattern: ^\d+\.\d+$ |
| name | string | Yes | 1-200 chars, = source_term |
| attributes.canonical_translation | string | No | Null if uncertain |
| attributes.source_term | string | Yes | Exact source surface form |
| attributes.domain_tags | array[string] | Yes | Controlled vocabulary |
| attributes.part_of_speech | string | Yes | Enum: noun/verb/adjective/adverb/proper_noun/phrase/idiom/other |
| attributes.context_rules | object | Yes | May be empty |
| attributes.forbidden_forms | array[string] | Yes | May be empty |
| attributes.aliases | array[string] | Yes | May be empty |
| attributes.notes | string | No | Always null at extraction |
| attributes.relationships | object | Yes | May be empty |
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
| No terms found | Empty extraction result | Return empty array [] |
| Schema validation failure | JSON Schema validation | Return error object with error_code: SCHEMA_VIOLATION |
| Confidence below threshold | confidence < 0.3 | Include but flag with review_status: needs_review |
| Ambiguous category | Term fits multiple categories | Extract with primary category; list alternatives in tags |
| Missing translation | No canonical_translation proposed | Set to null; flag for review |
| Missing required field | Required field absent | Return error object with error_code: MISSING_FIELD |

Error Object Format:
`json
{
  error: true,
  error_code: <CODE>,
  message: <description>,
  source_location: <location>,
  partial_results: []
}
`

---

## 6. Confidence Rules

| Evidence Level | Confidence Range | Criteria |
|----------------|------------------|----------|
| Explicit term + clear context + translation obvious | 0.9 - 1.0 | Full direct evidence |
| Explicit term + clear context | 0.7 - 0.89 | Strong evidence |
| Explicit term + ambiguous context | 0.5 - 0.69 | Moderate evidence |
| Term only (no context clues) | 0.3 - 0.49 | Weak evidence |
| Ambiguous/uncertain | 0.0 - 0.29 | Flag for review |

**Confidence Calculation**:
- Start at 0.5 for explicit term mention
- +0.3 for clear contextual definition/usage
- +0.2 for recognizable category markers
- +0.1 for recurring term in same segment
- -0.3 for isolated mention without context
- -0.2 for ambiguous category
- Clamp to [0.0, 1.0]

---

## 7. Duplicate Rules

| Rule ID | Rule | Action |
|---------|------|--------|
| GL-DUP-01 | Same source_term + same source_location | Merge into single entity |
| GL-DUP-02 | Same source_term + adjacent source_location (same chapter) | Merge; update source_location to range |
| GL-DUP-03 | Different surface form, same canonical concept (alias) | Single entity; add surface form to aliases |
| GL-DUP-04 | Cross-chapter same term | Separate entities; link via references later |
| GL-DUP-05 | entity_id collision (deterministic hash) | Append sequence suffix |

**Merge Strategy**: 
- Keep highest confidence
- Union of domain_tags
- Union of aliases
- Union of forbidden_forms
- Most specific canonical_translation
- Updated source_location to encompass range

---

## 8. Determinism Guarantees

- Temperature = 0 (conceptual)
- No random seeds
- Fixed prompt template
- Deterministic UUID generation: uuidv5(namespace, source_location + | + source_term)
- Fixed field ordering in JSON output (alphabetical keys)
- No timestamp variance (use fixed extraction_timestamp for reproducibility)

---

## 9. Schema Compliance Checklist

- [ ] All required fields present
- [ ] entity_type = glossary (const)
- [ ] schema_version = 1.0
- [ ] part_of_speech in enum
- [ ] confidence in [0.0, 1.0]
- [ ] created_at, updated_at ISO8601
- [ ] version >= 1
- [ ] additionalProperties = false respected
- [ ] UUIDv4 format for entity_id
- [ ] No extra fields beyond schema

---

*End of Glossary Extractor Prompt Design*
