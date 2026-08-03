# RM-5.8.0 — Golden Dataset Specification

## Overview

This document defines the **Golden Dataset Specification** for the Knowledge Benchmark Framework. The golden dataset serves as the ground truth against which all Knowledge Extractor outputs are measured.

**Scope**: Format definition only. No bulk data creation in this stage.

---

## Extractor Coverage

Five Knowledge Extractors, each with dedicated golden dataset:

| Extractor | Directory | Purpose |
|-----------|-----------|---------|
| Character | `benchmarks/golden/character/` | Character profiles, relationships, attributes |
| Glossary | `benchmarks/golden/glossary/` | Terms, definitions, translations, context |
| Scene | `benchmarks/golden/scene/` | Locations, atmosphere, sensory details |
| Narrative | `benchmarks/golden/narrative/` | Plot points, story arcs, pacing |
| Style | `benchmarks/golden/style/` | Writing style, tone, literary devices |

---

## Difficulty Tiers

Each extractor has three difficulty tiers:

| Tier | Description | Example Characteristics |
|------|-------------|------------------------|
| **Easy** | Clear, explicit information | Direct character descriptions, explicit term definitions |
| **Medium** | Implicit, requires inference | Implied relationships, contextual term usage |
| **Hard** | Ambiguous, multi-hop reasoning | Contradictory info, subtle style markers, complex narratives |
---

## Entity Schema (Per Extractor)

### Character Entity
```json
{
  "id": "string",
  "type": "character",
  "name": "string",
  "aliases": ["string"],
  "attributes": {"key": "value"},
  "relationships": [{"target": "string", "type": "string"}],
  "appearances": [{"chapter": "int", "context": "string"}]
}
```

### Glossary Entity
```json
{
  "id": "string",
  "type": "glossary",
  "term": "string",
  "definition": "string",
  "translation": "string",
  "context": "string",
  "category": "string",
  "variants": ["string"]
}
```

### Scene Entity
```json
{
  "id": "string",
  "type": "scene",
  "location": "string",
  "atmosphere": "string",
  "sensory_details": {"visual": "", "auditory": "", "olfactory": ""},
  "time_of_day": "string",
  "significance": "string"
}
```

### Narrative Entity
```json
{
  "id": "string",
  "type": "narrative",
  "plot_point": "string",
  "arc": "string",
  "tension_level": "float",
  "pacing": "string",
  "foreshadowing": ["string"]
}
```

### Style Entity
```json
{
  "id": "string",
  "type": "style",
  "tone": "string",
  "literary_devices": ["string"],
  "sentence_patterns": ["string"],
  "vocabulary_level": "string",
  "rhythm": "string"
}
```

---

## Directory Layout

```
benchmarks/golden/
├── character/
│   ├── easy/
│   │   ├── character_easy_001.json
│   │   ├── character_easy_002.json
│   │   └── ...
│   ├── medium/
│   └── hard/
├── glossary/
│   ├── easy/
│   ├── medium/
│   └── hard/
├── scene/
│   ├── easy/
│   ├── medium/
│   └── hard/
├── narrative/
│   ├── easy/
│   ├── medium/
│   └── hard/
└── style/
    ├── easy/
    ├── medium/
    └── hard/
```

---

## Minimum Entry Counts (Per Extractor)

| Difficulty | Minimum Entries |
|------------|-----------------|
| Easy | 10 |
| Medium | 10 |
| Hard | 5 |
| **Total per Extractor** | **25** |
| **Grand Total (5 Extractors)** | **125** |

---

## Versioning & Immutability

- **Golden Dataset Version**: Semantic version (e.g., `v1.0.0`)
- **Immutability Rule**: Once a version is baselined, entries **must not be modified**
- **New Versions**: Create new version directory (e.g., `v1.1.0/`) for corrections/additions
- **Baseline Binding**: Each baseline score is bound to a specific golden dataset version

---

## Validation Rules

1. All `benchmark_id` must be unique within an extractor
2. `expected_entities` must match entity IDs in `expected_output.entities`
3. `expected_confidence.mean` must be within `[min, max]`
4. `input.text` must be non-empty
5. At least one entity per entry
6. Schema validation against extractor-specific entity schema

---

## Acceptance Criteria for This Document

- [ ] Schema defined for all 5 extractors
- [ ] Difficulty tiers defined
- [ ] Directory structure specified
- [ ] Minimum entry counts specified
- [ ] Versioning and immutability rules defined
- [ ] Validation rules specified