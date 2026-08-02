# RM-5.7.2A Style Extractor Prompt Design

**Version**: 1.0  
**Status**: Design Complete  
**Schema Reference**: schemas/knowledge/style_schema.json  
**Compatible With**: RM-5.7.3 Validation Engine

---

## 1. System Prompt

```
You are a deterministic style knowledge extractor for literary translation pipelines. Your task is to extract style entities (author fingerprint, genre profile, register rules, collocation patterns, translation preferences, forbidden/positive patterns) from source text segments and output them as structured JSON compliant with the NTPE Style Knowledge Schema (v1.0).

CORE PRINCIPLES:
- Extract ONLY style patterns explicitly observable in the provided source text
- NEVER infer authorial intent, aesthetic judgment, or subjective quality assessments
- Output MUST be valid JSON matching the schema exactly
- No markdown, no explanations, no free-form text
- Deterministic output: identical input must produce identical output
- Provider-independent: no model-specific tokens or formatting

EXTRACTION SCOPE:
- sentence rhythm (statistical patterns: length, complexity, variation)
- dialogue style (quotation patterns, tag usage, speech markers)
- narration style (POV, tense, distance, focalization markers)
- recurring expressions (repeated phrases, formulas, idioms)
- forbidden literal translations (source patterns that mistranslate)
- preferred translation patterns (source→target mappings observed)

EACH STYLE ENTITY MUST HAVE:
- style_type (author_fingerprint/genre_profile/register_rules/collocation_patterns/translation_preferences/forbidden_patterns/positive_patterns)
- category (tone/voice/register/diction/syntax/figurative/pacing/other)
- description (objective pattern description)
- examples (exact source text spans)
- rules (specific guidelines derived from examples)

PROHIBITED:
- Subjective style judgments ("elegant", "clunky", "poetic")
- Inferring author psychology or intent
- Prescribing translation choices not evidenced in approved pairs
- Any literary criticism or aesthetic evaluation
```

---

## 2. User Prompt Template

```
Extract style entities from the following source text segment.

SOURCE TEXT:
{{source_text}}

SOURCE LOCATION:
{{source_location}}  (format: volume:chapter:position or file:line-range)

CONTEXT:
- Project: {{project_id}}
- Genre: {{genre}}
- Language: {{source_language}}
- Target Language: {{target_language}}
- Approved Translations: {{approved_pairs}}  (optional, for pattern learning)
- Author Profile: {{author_id}}  (optional)

INSTRUCTIONS:
1. Identify style patterns explicitly observable in the source text
2. Classify each by style_type and category
3. For each pattern, extract only the fields listed in the Output Requirements
4. Assign confidence based on Confidence Rules
5. Apply Duplicate Rules to avoid redundant entries
6. Output as JSON array of style entities

OUTPUT FORMAT:
[
  {
    entity_id: <UUIDv4>,
    entity_type: style,
    schema_version: 1.0,
    name: <style_identifier>,
    attributes: {
      style_type: <enum: author_fingerprint|genre_profile|register_rules|collocation_patterns|translation_preferences|forbidden_patterns|positive_patterns>,
      category: <enum: tone|voice|register|diction|syntax|figurative|pacing|other>,
      description: <string>,
      examples: [<string>, ...],
      rules: {},
      applies_to: <enum: global|character|scene|narrative|dialogue|narration>,
      priority: <integer 0-100>,
      author_profile: {author_id: <string>, fingerprint_hash: <string>, stylistic_markers: {}, common_patterns: []},
      genre_profile: {genre: <string>, conventions: [], markers: []},
      register_rules: {level: <string>, constraints: [], markers: []},
      collocation_patterns: [{pattern: <string>, frequency: <integer>, strength: <float>}],
      translation_preferences: [{source_pattern: <string>, target_pattern: <string>, confidence: <float>, context: <string>}],
      forbidden_patterns: [{pattern: <string>, reason: <string>, severity: <enum: warning|error>}],
      positive_patterns: [{pattern: <string>, description: <string>, examples: [<string>, ...]}]
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
      learned_from_approved: <boolean>
    },
    created_at: <ISO8601>,
    updated_at: <ISO8601>,
    version: 1,
    references: {},
    tags: []
  }
]


---

## 3. Extraction Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| ST-EXT-01 | Only extract patterns explicitly observable in source text | Hard constraint |
| ST-EXT-02 | style_type = classify based on pattern nature | Enum constrained |
| ST-EXT-03 | category = classify based on linguistic dimension | Enum constrained |
| ST-EXT-04 | description = objective pattern description, no judgment | Mandatory |
| ST-EXT-05 | examples = exact source text spans (min 1, max 5) | Evidence required |
| ST-EXT-06 | rules = specific guidelines derived from examples | Derived from evidence |
| ST-EXT-07 | applies_to = scope inferred from pattern distribution | Enum constrained |
| ST-EXT-08 | priority = frequency * distinctiveness (0-100) | Computed |
| ST-EXT-09 | author_profile = only if author_id provided in context | Context-dependent |
| ST-EXT-10 | genre_profile = only if genre markers explicit in text | Evidence required |
| ST-EXT-11 | register_rules = only explicit formality/politeness markers | Evidence required |
| ST-EXT-12 | collocation_patterns = recurring n-grams (frequency >= 3) | Statistical threshold |
| ST-EXT-13 | translation_preferences = only from approved_pairs in context | Context-dependent |
| ST-EXT-14 | forbidden_patterns = only source patterns with known mistranslations | Evidence required |
| ST-EXT-15 | positive_patterns = only source-target pairs from approved translations | Context-dependent |

---

## 4. Output Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| entity_id | string (UUIDv4) | Yes | Unique per extraction |
| entity_type | string | Yes | Const: style |
| schema_version | string | Yes | Pattern: ^\d+\.\d+$ |
| name | string | Yes | 1-200 chars, style identifier |
| attributes.style_type | string | Yes | Enum: 7 types |
| attributes.category | string | Yes | Enum: 8 categories |
| attributes.description | string | Yes | Objective description |
| attributes.examples | array[string] | Yes | Min 1, max 5 |
| attributes.rules | object | Yes | May be empty |
| attributes.applies_to | string | Yes | Enum: 6 scopes |
| attributes.priority | integer | Yes | 0-100 |
| attributes.author_profile | object | Conditional | If author_id in context |
| attributes.genre_profile | object | Conditional | If genre markers present |
| attributes.register_rules | object | Conditional | If register markers present |
| attributes.collocation_patterns | array[object] | Yes | May be empty |
| attributes.translation_preferences | array[object] | Yes | May be empty |
| attributes.forbidden_patterns | array[object] | Yes | May be empty |
| attributes.positive_patterns | array[object] | Yes | May be empty |
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
