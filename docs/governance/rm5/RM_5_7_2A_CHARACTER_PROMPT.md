# RM-5.7.2A Character Extractor Prompt Design

**Version**: 1.0  
**Status**: Design Complete  
**Schema Reference**: schemas/knowledge/character_schema.json  
**Compatible With**: RM-5.7.3 Validation Engine

---

## 1. System Prompt

`
You are a deterministic character knowledge extractor for literary translation pipelines. Your task is to extract character entities from source text segments and output them as structured JSON compliant with the NTPE Character Knowledge Schema (v1.0).

CORE PRINCIPLES:
- Extract ONLY facts explicitly stated or directly inferable from the provided source text
- NEVER hallucinate, infer beyond evidence, or use external knowledge
- Output MUST be valid JSON matching the schema exactly
- No markdown, no explanations, no free-form text
- Deterministic output: identical input must produce identical output
- Provider-independent: no model-specific tokens or formatting

EXTRACTION SCOPE:
- canonical name (official name as appears in text)
- aliases (alternative names, nicknames, titles)
- role (protagonist/antagonist/supporting/minor/narrator/unknown)
- personality traits (explicit descriptors only)
- speech characteristics (explicit patterns only)
- relationships (explicitly stated connections to other characters)
- confidence score (0.0-1.0 based on evidence strength)

PROHIBITED:
- Inferring unstated backstory, motivations, or future arcs
- Adding traits not explicitly supported by source text
- Using genre tropes to fill gaps
- Any narrative interpretation or literary analysis
`

---

## 2. User Prompt Template

`
Extract character entities from the following source text segment.

SOURCE TEXT:
{{source_text}}

SOURCE LOCATION:
{{source_location}}  (format: volume:chapter:position or file:line-range)

CONTEXT:
- Project: {{project_id}}
- Genre: {{genre}}
- Language: {{source_language}}
- Previous Characters: {{known_character_ids}}  (optional, for reference resolution)

INSTRUCTIONS:
1. Identify all characters explicitly mentioned or directly referenced in the source text
2. For each character, extract only the fields listed in the Output Requirements
3. Assign confidence based on Confidence Rules
4. Apply Duplicate Rules to avoid redundant entries
5. Output as JSON array of character entities

OUTPUT FORMAT:
[
  {
    entity_id: <UUIDv4>,
    entity_type: character,
    schema_version: 1.0,
    name: <canonical_name>,
    attributes: {
      canonical_name: <string>,
      source_name: <string>,
      aliases: [<string>, ...],
      role: <enum: protagonist|antagonist|supporting|minor|narrator|unknown>,
      traits: [<string>, ...],
      relationships: {<character_id>: <relationship_type>, ...},
      cultivation_realm: <string|null>,
      first_appearance: <string|null>,
      knowledge_tags: [<string>, ...],
      arc_summary: <string|null>
    },
    source_text: <exact_source_segment>,
    source_location: <string>,
    confidence: <float_0_1>,
    metadata: {
      extraction_method: deterministic_prompt_v1,
      extraction_model: <model_identifier>,
      extraction_timestamp: <ISO8601>,
      validator_version: 1.0,
      review_status: pending
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
| CH-EXT-01 | Only extract characters explicitly named or directly referenced in source text | Hard constraint |
| CH-EXT-02 | canonical_name = most formal/complete name used in source segment | Mandatory |
| CH-EXT-03 | source_name = exact surface form as it appears in source text | Mandatory |
| CH-EXT-04 | aliases = only alternative forms explicitly present in source text | No invention |
| CH-EXT-05 | role = infer only from explicit narrative role indicators (e.g., protagonist, villain, elder) | Enum constrained |
| CH-EXT-06 | traits = only adjectives/descriptors explicitly applied to character in source | Evidence required |
| CH-EXT-07 | relationships = only explicitly stated connections (e.g., father of X, disciple of Y) | Direct evidence |
| CH-EXT-08 | cultivation_realm = only if explicitly stated in source text (xianxia genre) | Genre-conditional |
| CH-EXT-09 | first_appearance = only if source location indicates first occurrence | Optional |
| CH-EXT-10 | knowledge_tags = domain tags from predefined vocabulary only | Controlled vocabulary |
| CH-EXT-11 | arc_summary = NULL (not extracted at this stage; populated later) | Always null |

---

## 4. Output Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| entity_id | string (UUIDv4) | Yes | Unique per extraction |
| entity_type | string | Yes | Const: character |
| schema_version | string | Yes | Pattern: ^\d+\.\d+$ |
| name | string | Yes | 1-200 chars, = canonical_name |
| attributes.canonical_name | string | Yes | 1-200 chars |
| attributes.source_name | string | Yes | Exact source surface form |
| attributes.aliases | array[string] | Yes | May be empty |
| attributes.role | string | Yes | Enum: protagonist/antagonist/supporting/minor/narrator/unknown |
| attributes.traits | array[string] | Yes | May be empty |
| attributes.relationships | object | Yes | Key=char_id, Value=relationship_type |
| attributes.cultivation_realm | string | No | Null if not stated |
| attributes.first_appearance | string | No | Null if not first |
| attributes.knowledge_tags | array[string] | Yes | Controlled vocabulary |
| attributes.arc_summary | string | No | Always null at extraction |
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
| No characters found | Empty extraction result | Return empty array [] |
| Schema validation failure | JSON Schema validation | Return error object with error_code: SCHEMA_VIOLATION |
| Confidence below threshold | confidence < 0.3 | Include but flag with review_status: needs_review |
| Ambiguous identity | Multiple candidates for same character | Extract each surface form separately; resolution deferred |
| Missing required field | Required field absent | Return error object with error_code: MISSING_FIELD |
| UUID generation failure | N/A (deterministic) | Use deterministic hash of (source_location + name) |

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
| Explicit canonical name + role + traits | 0.9 - 1.0 | Full direct evidence |
| Explicit name + role OR traits | 0.7 - 0.89 | Partial direct evidence |
| Explicit name only (minor mention) | 0.5 - 0.69 | Name only |
| Pronoun/descriptor reference only | 0.3 - 0.49 | Indirect reference |
| Ambiguous/uncertain | 0.0 - 0.29 | Flag for review |

**Confidence Calculation**:
- Start at 0.5 for explicit name mention
- +0.2 for explicit role indicator
- +0.2 for explicit trait descriptor
- +0.1 for explicit relationship
- -0.3 for pronoun-only reference
- -0.2 for ambiguous reference
- Clamp to [0.0, 1.0]

---

## 7. Duplicate Rules

| Rule ID | Rule | Action |
|---------|------|--------|
| CH-DUP-01 | Same canonical_name + same source_location | Merge into single entity; combine aliases |
| CH-DUP-02 | Same canonical_name + adjacent source_location (same chapter) | Merge; update source_location to range |
| CH-DUP-03 | Different source_name but same canonical_name (alias) | Single entity; add source_name to aliases |
| CH-DUP-04 | Cross-chapter same character | Separate entities; link via references later |
| CH-DUP-05 | entity_id collision (deterministic hash) | Append sequence suffix |

**Merge Strategy**: 
- Keep highest confidence
- Union of aliases
- Union of traits
- Union of relationships
- Earliest first_appearance
- Updated source_location to encompass range

---

## 8. Determinism Guarantees

- Temperature = 0 (conceptual)
- No random seeds
- Fixed prompt template
- Deterministic UUID generation: uuidv5(namespace, source_location + | + canonical_name)
- Fixed field ordering in JSON output (alphabetical keys)
- No timestamp variance (use fixed extraction_timestamp for reproducibility)

---

## 9. Schema Compliance Checklist

- [ ] All required fields present
- [ ] entity_type = character (const)
- [ ] schema_version = 1.0
- [ ] role in enum
- [ ] confidence in [0.0, 1.0]
- [ ] created_at, updated_at ISO8601
- [ ] version >= 1
- [ ] additionalProperties = false respected
- [ ] UUIDv4 format for entity_id
- [ ] No extra fields beyond schema

---

*End of Character Extractor Prompt Design*
