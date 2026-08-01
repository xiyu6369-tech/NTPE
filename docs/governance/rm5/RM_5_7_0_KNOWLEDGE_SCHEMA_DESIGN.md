# RM-5.7.0 Knowledge Schema Design

**Baseline**: RM-5.7.0 Architecture Baseline  
**Version**: RM-5.7.0  
**Status**: Schema Governance  
**Created**: 2026-08-02  
**Purpose**: Formal schema definitions for all knowledge entities — glossary, character, narrative, and style domains.

---

## 1. Schema Design Principles

| Principle | Rule |
|-----------|------|
| **Explicit over Implicit** | All fields declared; no dynamic properties |
| **Reference Integrity** | Cross-entity links use UUIDv4; validated at compile time |
| **Versioned Evolution** | Every entity carries `schema_version`; migrations are explicit |
| **Human-Readable** | JSON with descriptive field names; no minification in source |
| **Machine-Validatable** | JSON Schema Draft 2020-12; CI validation on every change |

---

## 2. Base Schema (`base.schema.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/base.schema.json",
  "title": "NTPE Knowledge Base Entity",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique entity identifier (UUIDv4)"
    },
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version of entity schema"
    },
    "domain": {
      "type": "string",
      "enum": ["glossary", "character", "narrative", "style"],
      "description": "Knowledge domain"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Entity creation timestamp (ISO 8601)"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Last modification timestamp (ISO 8601)"
    },
    "source_refs": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Source document references (file:line-range)"
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Extraction/validation confidence score"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "validated", "approved", "deprecated"],
---

## 3. Glossary Schema (`glossary.schema.json`)

### 3.1 Term Entity

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/glossary.schema.json",
  "title": "Glossary Term",
  "allOf": [
    { "$ref": "base.schema.json" },
    {
      "type": "object",
      "properties": {
        "domain": { "const": "glossary" },
        "canonical": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Authoritative term form (target language)"
        },
        "source_term": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Original term in source language"
        },
        "domain_tags": {
          "type": "array",
          "items": { "type": "string", "enum": ["cultivation", "modern", "historical", "fantasy", "system", "medical", "military", "political", "romance", "general"] },
          "description": "Semantic domain classifications"
        },
        "part_of_speech": {
          "type": "string",
          "enum": ["noun", "verb", "adjective", "adverb", "proper_noun", "phrase", "honorific", "title"],
          "description": "Grammatical category"
        },
        "context_rules": {
          "type": "array",
          "items": { "$ref": "#/$defs/contextRule" },
          "description": "Conditional translation rules"
        },
        "aliases": {
          "type": "array",
          "items": { "$ref": "#/$defs/alias" },
          "description": "Alternative forms and variants"
        },
        "forbidden_forms": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Forms that must never appear in output"
        },
        "notes": {
          "type": "string",
          "description": "Translator notes and usage guidance"
        }
      },
      "required": ["canonical", "source_term", "domain_tags", "part_of_speech"],
      "additionalProperties": false
    }
  ],
  "$defs": {
    "alias": {
      "type": "object",
      "properties": {
        "form": { "type": "string", "minLength": 1 },
        "language": { "type": "string", "enum": ["zh-CN", "zh-TW", "en", "ko", "ja"] },
        "status": { "type": "string", "enum": ["canonical", "variant", "deprecated", "error"] },
        "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
      },
      "required": ["form", "language", "status"],
      "additionalProperties": false
    },
    "contextRule": {
      "type": "object",
      "properties": {
        "condition": { "type": "string", "description": "Natural language condition" },
        "translation": { "type": "string", "description": "Context-specific translation" },
        "priority": { "type": "integer", "minimum": 1, "maximum": 10 }
      },
      "required": ["condition", "translation", "priority"],
      "additionalProperties": false
    }
  }
}
```

### 3.2 Glossary Business Rules

| Rule ID | Rule | Validation |
|---------|------|------------|
---

## 4. Character Schema (`character.schema.json`)

### 4.1 Character Entity

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/character.schema.json",
  "title": "Character",
  "allOf": [
    { "$ref": "base.schema.json" },
    {
      "type": "object",
      "properties": {
        "domain": { "const": "character" },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 50,
          "description": "Canonical character name (target language)"
        },
        "source_name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 50,
          "description": "Original character name (source language)"
        },
        "aliases": {
          "type": "array",
          "items": { "$ref": "#/$defs/alias" },
          "description": "Name variants, titles, nicknames"
        },
        "role": {
          "type": "string",
          "enum": ["protagonist", "antagonist", "supporting", "minor", "narrator", "system"],
          "description": "Narrative role classification"
        },
        "traits": {
          "type": "array",
          "items": { "$ref": "#/$defs/trait" },
          "description": "Personality, physical, and behavioral traits"
        },
        "relationships": {
          "type": "array",
          "items": { "$ref": "#/$defs/relationship" },
          "description": "Character-to-character relationships"
        },
        "arc_summary": {
          "type": "string",
          "description": "High-level character arc description"
        },
        "first_appearance": {
          "type": "string",
          "description": "Volume/chapter reference for first appearance"
        },
        "knowledge_tags": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Tags for knowledge retrieval (cultivation_realm, faction, etc.)"
        }
      },
      "required": ["name", "source_name", "role", "first_appearance"],
      "additionalProperties": false
    }
  ],
  "$defs": {
    "alias": {
      "type": "object",
      "properties": {
        "form": { "type": "string", "minLength": 1 },
        "type": { "type": "string", "enum": ["name", "title", "nickname", "honorific", "cultivation_title"] },
        "language": { "type": "string", "enum": ["zh-CN", "zh-TW", "en", "ko", "ja"] },
        "context": { "type": "string", "description": "When this alias is used" }
      },
      "required": ["form", "type", "language"],
      "additionalProperties": false
    },
    "trait": {
      "type": "object",
      "properties": {
        "category": { "type": "string", "enum": ["personality", "physical", "ability", "background", "speech_pattern"] },
        "key": { "type": "string", "description": "Trait identifier (e.g., 'cold_pragmatist')" },
        "value": { "type": "string", "description": "Trait description" },
        "evidence_refs": { "type": "array", "items": { "type": "string" } },
        "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
      },
      "required": ["category", "key", "value"],
      "additionalProperties": false
    },
    "relationship": {
      "type": "object",
      "properties": {
        "target_character_id": { "type": "string", "format": "uuid" },
        "type": { "type": "string", "enum": ["family", "romantic", "rival", "ally", "enemy", "master_disciple", "faction", "system"] },
        "description": { "type": "string" },
        "bidirectional": { "type": "boolean", "default": false },
        "strength": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
      },
      "required": ["target_character_id", "type", "description"],
      "additionalProperties": false
    }
  }
}
```

### 4.2 Character Business Rules

| Rule ID | Rule | Validation |
|---------|------|------------|
---

## 5. Narrative Schema (`narrative.schema.json`)

### 5.1 Scene Entity

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/narrative.schema.json",
  "title": "Narrative Elements",
  "allOf": [
    { "$ref": "base.schema.json" },
    {
      "type": "object",
      "properties": {
        "domain": { "const": "narrative" },
        "entity_type": { "type": "string", "enum": ["scene", "plot_point", "timeline", "world_rule"] }
      },
      "discriminator": { "propertyName": "entity_type", "mapping": {
        "scene": "#/$defs/scene",
        "plot_point": "#/$defs/plotPoint",
        "timeline": "#/$defs/timeline",
        "world_rule": "#/$defs/worldRule"
      }}
    }
  ],
  "$defs": {
    "scene": {
      "type": "object",
      "properties": {
        "domain": { "const": "narrative" },
        "entity_type": { "const": "scene" },
        "scene_id": { "type": "string", "pattern": "^SC-\\d+$" },
        "title": { "type": "string", "maxLength": 100 },
        "volume": { "type": "integer", "minimum": 1 },
        "chapter_range": { "type": "string", "pattern": "^\\d+(-\\d+)?$" },
        "location": { "type": "string" },
        "time_of_day": { "type": "string", "enum": ["dawn", "morning", "noon", "afternoon", "evening", "night", "late_night", "unknown"] },
        "participating_characters": { "type": "array", "items": { "type": "string", "format": "uuid" } },
        "plot_points": { "type": "array", "items": { "type": "string", "format": "uuid" } },
        "summary": { "type": "string" },
        "tone": { "type": "string", "enum": ["tense", "peaceful", "melancholic", "action", "romantic", "comedic", "horror", "mystery"] }
      },
      "required": ["scene_id", "volume", "chapter_range", "participating_characters"],
      "additionalProperties": false
    },
    "plotPoint": {
      "type": "object",
      "properties": {
        "domain": { "const": "narrative" },
        "entity_type": { "const": "plot_point" },
        "plot_id": { "type": "string", "pattern": "^PP-\\d+$" },
        "title": { "type": "string", "maxLength": 100 },
        "type": { "type": "string", "enum": ["inciting", "rising", "climax", "falling", "resolution", "revelation", "twist", "setup"] },
        "description": { "type": "string" },
        "affected_characters": { "type": "array", "items": { "type": "string", "format": "uuid" } },
        "prerequisite_plots": { "type": "array", "items": { "type": "string", "format": "uuid" } },
        "consequence_plots": { "type": "array", "items": { "type": "string", "format": "uuid" } },
        "timeline_position": { "type": "number", "description": "Normalized 0.0-1.0 position in narrative arc" }
      },
      "required": ["plot_id", "type", "description", "timeline_position"],
      "additionalProperties": false
    },
    "timeline": {
      "type": "object",
      "properties": {
        "domain": { "const": "narrative" },
        "entity_type": { "const": "timeline" },
        "timeline_id": { "type": "string", "pattern": "^TL-\\d+$" },
        "name": { "type": "string" },
        "events": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "position": { "type": "number" },
              "event_id": { "type": "string", "format": "uuid" },
              "event_type": { "type": "string", "enum": ["scene", "plot_point", "character_milestone"] },
              "description": { "type": "string" }
            },
            "required": ["position", "event_id", "event_type"]
          }
        }
      },
      "required": ["timeline_id", "events"],
      "additionalProperties": false
    },
    "worldRule": {
      "type": "object",
      "properties": {
        "domain": { "const": "narrative" },
        "entity_type": { "const": "world_rule" },
        "rule_id": { "type": "string", "pattern": "^WR-\\d+$" },
        "category": { "type": "string", "enum": ["cultivation_system", "magic_system", "political_structure", "geography", "history", "technology", "social_custom"] },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "constraints": { "type": "array", "items": { "type": "string" } },
        "exceptions": { "type": "array", "items": { "type": "string" } },
        "source_volume": { "type": "integer" }
      },
      "required": ["rule_id", "category", "name", "description"],
      "additionalProperties": false
    }
---

## 6. Style Schema (`style.schema.json`)

### 6.1 ToneProfile Entity

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/style.schema.json",
  "title": "Style and Tone Definitions",
  "allOf": [
    { "$ref": "base.schema.json" },
    {
      "type": "object",
      "properties": {
        "domain": { "const": "style" },
        "entity_type": { "type": "string", "enum": ["tone_profile", "register_rule", "formatting_convention"] }
      },
      "discriminator": { "propertyName": "entity_type", "mapping": {
        "tone_profile": "#/$defs/toneProfile",
        "register_rule": "#/$defs/registerRule",
        "formatting_convention": "#/$defs/formattingConvention"
      }}
    }
  ],
  "$defs": {
    "toneProfile": {
      "type": "object",
      "properties": {
        "domain": { "const": "style" },
        "entity_type": { "const": "tone_profile" },
        "profile_id": { "type": "string", "pattern": "^TP-\\d+$" },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "dimensions": {
          "type": "object",
          "properties": {
            "formality": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
            "emotionality": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
            "verbosity": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
            "archaic_level": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
            "poetic_density": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
          },
          "required": ["formality", "emotionality", "verbosity", "archaic_level", "poetic_density"]
        },
        "applicable_contexts": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["profile_id", "name", "dimensions"],
      "additionalProperties": false
    },
    "registerRule": {
      "type": "object",
      "properties": {
        "domain": { "const": "style" },
        "entity_type": { "const": "register_rule" },
        "rule_id": { "type": "string", "pattern": "^RR-\\d+$" },
        "trigger": { "type": "string", "enum": ["character_role", "scene_tone", "dialogue_vs_narrative", "cultivation_realm", "relationship_intimacy"] },
        "condition": { "type": "string" },
        "adjustments": {
          "type": "object",
          "properties": {
            "formality_delta": { "type": "number", "minimum": -1.0, "maximum": 1.0 },
            "honorific_required": { "type": "boolean" },
            "pronoun_style": { "type": "string", "enum": ["formal", "informal", "intimate", "reverent"] }
          }
        }
      },
      "required": ["rule_id", "trigger", "condition", "adjustments"],
      "additionalProperties": false
    },
    "formattingConvention": {
      "type": "object",
      "properties": {
        "domain": { "const": "style" },
        "entity_type": { "const": "formatting_convention" },
        "convention_id": { "type": "string", "pattern": "^FC-\\d+$" },
        "name": { "type": "string" },
        "scope": { "type": "string", "enum": ["global", "dialogue", "internal_monologue", "system_message", "chapter_title"] },
        "rules": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": { "type": "string" },
              "replacement": { "type": "string" },
              "description": { "type": "string" }
            },
            "required": ["pattern", "replacement", "description"]
          }
        }
      },
      "required": ["convention_id", "name", "scope", "rules"],
      "additionalProperties": false
    }
---

## 7. Manifest Schema (`manifest.schema.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ntpe.ai/schemas/knowledge/manifest.schema.json",
  "title": "Knowledge Manifest",
  "type": "object",
  "properties": {
    "manifest_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "generated_at": { "type": "string", "format": "date-time" },
    "generator_version": { "type": "string" },
    "schema_versions": {
      "type": "object",
      "properties": {
        "base": { "type": "string" },
        "glossary": { "type": "string" },
        "character": { "type": "string" },
        "narrative": { "type": "string" },
        "style": { "type": "string" }
      },
      "required": ["base", "glossary", "character", "narrative", "style"]
    },
    "domains": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "domain": { "type": "string", "enum": ["glossary", "character", "narrative", "style"] },
          "artifact_path": { "type": "string" },
          "entity_count": { "type": "integer", "minimum": 0 },
          "checksum_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
          "size_bytes": { "type": "integer", "minimum": 0 }
        },
        "required": ["domain", "artifact_path", "entity_count", "checksum_sha256", "size_bytes"]
      }
    },
    "validation_summary": {
      "type": "object",
      "properties": {
        "schema_valid": { "type": "boolean" },
        "cross_refs_valid": { "type": "boolean" },
        "business_rules_passed": { "type": "integer" },
        "business_rules_failed": { "type": "integer" },
        "warnings": { "type": "integer" }
      },
      "required": ["schema_valid", "cross_refs_valid", "business_rules_passed", "business_rules_failed", "warnings"]
    }
  },
  "required": ["manifest_version", "generated_at", "generator_version", "schema_versions", "domains", "validation_summary"],
  "additionalProperties": false
}
```

---

## 8. Schema Versioning Strategy

### 8.1 Version Format

All schemas use **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (field removal, type change, required field addition)
- **MINOR**: Backward-compatible additions (new optional fields, new enum values)
- **PATCH**: Bug fixes, documentation updates, non-functional changes

### 8.2 Compatibility Matrix

| Consumer Version | Producer Version | Compatible? | Migration Required |
|------------------|------------------|-------------|-------------------|
| 1.0.x | 1.0.y | Yes | No |
| 1.0.x | 1.1.y | Yes (forward) | Optional (new fields ignored) |
| 1.1.x | 1.0.y | No | Yes (missing required fields) |
| 1.x.y | 2.0.z | No | Yes (breaking changes) |

### 8.3 Migration Protocol

1. **Detection**: Manifest `schema_versions` compared against runtime expected versions
2. **Selection**: Appropriate migration script chosen (version-paired)
3. **Execution**: Entity-by-entity transformation with validation
4. **Verification**: Post-migration schema validation + spot-check sampling
5. **Commit**: New manifest generated with updated `schema_versions`

---

## 9. Validation Checklist

### 9.1 Schema Syntax

- [ ] All `.schema.json` files validate against JSON Schema meta-schema
- [ ] All `$ref` references resolve locally
- [ ] No circular references in schema definitions
- [ ] All `required` fields present in example instances

### 9.2 Business Rules

- [ ] GL-001 through GL-005 enforced
- [ ] CH-001 through CH-005 enforced
- [ ] Narrative cross-references (scene→plot_point, plot_point→character) resolve
- [ ] Style dimension values in [0.0, 1.0] range

### 9.3 Manifest Integrity

- [ ] All domain artifacts listed in manifest exist on disk
- [ ] SHA-256 checksums match actual file contents
- [ ] `entity_count` matches actual entity count in artifact
- [ ] `validation_summary.schema_valid` = true

---

## 10. References

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/
- RM-5.7.0 Architecture Baseline: `RM_5_7_0_KNOWLEDGE_GENERATION_ARCHITECTURE.md`
- Semantic Versioning: https://semver.org/
  }
}
```
  }
}
```
| CH-001 | name unique per project | Global uniqueness |
| CH-002 | relationship.target_character_id must exist | Referential integrity |
| CH-003 | No self-referential relationships | target_character_id ≠ self.id |
| CH-004 | aliases.form unique per (character, language, type) | Composite unique |
| CH-005 | cultivation_realm trait required for xianxia genre | Domain-specific rule |
| GL-001 | Canonical term unique per (source_term, domain_tags) | Composite unique constraint |
| GL-002 | No alias.form duplicates canonical within same language | Cross-field validation |
| GL-003 | context_rule.priority unique per term | Array uniqueness |
| GL-004 | forbidden_forms cannot include canonical | Negative constraint |
| GL-005 | confidence ≥ 0.7 for approved status | Threshold check |
      "description": "Lifecycle status"
    }
  },
  "required": ["id", "schema_version", "domain", "created_at", "updated_at", "status"],
  "additionalProperties": false
}
```