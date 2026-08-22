import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

# Style Prompt
style_content = """# RM-5.7.2A Style Extractor Prompt Design

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
- Subjective style judgments (\"elegant\", \"clunky\", \"poetic\")
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
"""

with open(os.path.join(base_path, "RM_5_7_2A_STYLE_PROMPT.md"), "w", encoding="utf-8") as f:
    f.write(style_content)

print("Style Part 1 written")