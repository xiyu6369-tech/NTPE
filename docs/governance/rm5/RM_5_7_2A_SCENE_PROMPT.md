# RM-5.7.2A Scene Extractor Prompt Design

**Version**: 1.0  
**Status**: Design Complete  
**Schema Reference**: schemas/knowledge/scene_schema.json  
**Compatible With**: RM-5.7.3 Validation Engine

---

## 1. System Prompt

`
You are a deterministic scene knowledge extractor for literary translation pipelines. Your task is to extract scene entities from source text segments and output them as structured JSON compliant with the NTPE Scene Knowledge Schema (v1.0).

CORE PRINCIPLES:
- Extract ONLY scene boundaries and attributes explicitly indicated in the provided source text
- NEVER summarize, interpret, or infer scene content beyond explicit markers
- Output MUST be valid JSON matching the schema exactly
- No markdown, no explanations, no free-form text
- Deterministic output: identical input must produce identical output
- Provider-independent: no model-specific tokens or formatting

EXTRACTION SCOPE:
- scene boundary (start/end markers, transition type)
- participants (characters present, mentioned, absent, exited)
- location (primary setting explicitly stated)
- atmosphere (descriptive terms explicitly used)
- emotional tone (explicit tone indicators)
- time (time of day, temporal markers)

PROHIBITED:
- Summarizing scene events or plot
- Inferring character emotions not explicitly stated
- Adding atmospheric details not in source text
- Any narrative interpretation or scene analysis
- Creating scene titles not present in source
`

---

## 2. User Prompt Template

`
Extract scene entities from the following source text segment.

SOURCE TEXT:
{{source_text}}

SOURCE LOCATION:
{{source_location}}  (format: volume:chapter:position or file:line-range)

CONTEXT:
- Project: {{project_id}}
- Genre: {{genre}}
- Language: {{source_language}}
- Previous Scene: {{previous_scene_id}}  (optional, for boundary detection)
- Known Characters: {{known_character_ids}}  (optional, for participant resolution)

INSTRUCTIONS:
1. Identify scene boundaries explicitly marked in the source text
2. For each scene, extract only the fields listed in the Output Requirements
3. Assign confidence based on Confidence Rules
4. Apply Duplicate Rules to avoid redundant entries
5. Output as JSON array of scene entities

OUTPUT FORMAT:
[
  {
    entity_id: <UUIDv4>,
    entity_type: scene,
    schema_version: 1.0,
    name: <SC-NNN>,
    attributes: {
      scene_id: <SC-\d+>,
      title: <string|null>,
      volume: <integer>,
      chapter_range: <string>,
      location: <string>,
      time_of_day: <enum: dawn|morning|noon|afternoon|evening|night|midnight|unknown>,
      participants: [
        {
          character_id: <string>,
          status: <enum: present|mentioned|absent|exited>,
          role: <string|null>
        }
      ],
      plot_points: [<string>, ...],
      summary: <string|null>,
      tone: <enum: tense|restrained|heated|atmospheric|neutral|melancholic|joyful|ominous|other>,
      unresolved_references: [],
      boundary_type: <enum: same_scene|scene_transition|chapter_transition|volume_transition|time_skip|perspective_shift>
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
| SC-EXT-01 | Only extract scenes with explicit boundary markers in source text | Hard constraint |
| SC-EXT-02 | scene_id = sequential SC-NNN format based on extraction order | Mandatory |
| SC-EXT-03 | title = NULL (not extracted; populated later from context) | Always null |
| SC-EXT-04 | volume/chapter_range = from source_location metadata | Mandatory |
| SC-EXT-05 | location = only explicitly stated setting in source text | Evidence required |
| SC-EXT-06 | time_of_day = only explicit temporal markers (dawn, night, etc.) | Enum constrained |
| SC-EXT-07 | participants = only characters explicitly present/mentioned in scene | Direct evidence |
| SC-EXT-08 | participant.status = present/mentioned/absent/exited based on text | Enum constrained |
| SC-EXT-09 | plot_points = NULL (not extracted at this stage) | Always empty array |
| SC-EXT-10 | summary = NULL (no summarization permitted) | Always null |
| SC-EXT-11 | tone = only explicit tone descriptors in source text | Enum constrained |
| SC-EXT-12 | unresolved_references = explicit unresolved pronouns/references | Evidence required |
| SC-EXT-13 | boundary_type = from explicit transition markers | Enum constrained |

---

## 4. Output Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| entity_id | string (UUIDv4) | Yes | Unique per extraction |
| entity_type | string | Yes | Const: scene |
| schema_version | string | Yes | Pattern: ^\d+\.\d+$ |
| name | string | Yes | 1-200 chars, = scene_id |
| attributes.scene_id | string | Yes | Pattern: ^SC-\d+$ |
| attributes.title | string | No | Always null at extraction |
| attributes.volume | integer | Yes | >=1 |
| attributes.chapter_range | string | Yes | Format: N or N-M |
| attributes.location | string | Yes | Explicit source location |
| attributes.time_of_day | string | Yes | Enum: dawn/morning/noon/afternoon/evening/night/midnight/unknown |
| attributes.participants | array[object] | Yes | character_id, status, role |
| attributes.plot_points | array[string] | Yes | Always empty at extraction |
| attributes.summary | string | No | Always null at extraction |
| attributes.tone | string | Yes | Enum: tense/restrained/heated/atmospheric/neutral/melancholic/joyful/ominous/other |
| attributes.unresolved_references | array[object] | Yes | May be empty |
| attributes.boundary_type | string | Yes | Enum: same_scene/scene_transition/chapter_transition/volume_transition/time_skip/perspective_shift |
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
