# RM-5.8.1 — Knowledge Benchmark Corpus Design

## Overview

This document defines the design of the **Knowledge Benchmark Corpus v1.0** for NTPE. The corpus provides standardized test data for the five Knowledge Extractors (Character, Glossary, Scene, Narrative, Style) enabling quantitative benchmarking of extraction quality.

**Critical Constraint**: This stage only creates the corpus framework and data. No Benchmark Runner, auto-scorer, or dashboard implementation. Runtime, Knowledge Layer, Validation, Review, and Compilation remain frozen.

---

## Corpus Architecture

### Directory Structure

```
benchmarks/golden/
├── character/
│   ├── easy/      (10 cases)
│   ├── medium/    (10 cases)
│   └── hard/      (10 cases)
├── glossary/
│   ├── easy/      (10 cases)
│   ├── medium/    (10 cases)
│   └── hard/      (10 cases)
├── scene/
│   ├── easy/      (10 cases)
│   ├── medium/    (10 cases)
│   └── hard/      (10 cases)
├── narrative/
│   ├── easy/      (10 cases)
│   ├── medium/    (10 cases)
│   └── hard/      (10 cases)
└── style/
    ├── easy/      (10 cases)
    ├── medium/    (10 cases)
    └── hard/      (10 cases)

benchmarks/spec/
├── benchmark_case_schema.json    # Unified schema for all cases
├── benchmark_manifest.json       # Corpus manifest with checksums
└── difficulty_definition.md      # Difficulty tier definitions

docs/governance/rm5/
├── RM_5_8_1_CORPUS_DESIGN.md       # This document
├── RM_5_8_1_CORPUS_GUIDELINE.md    # Creation guidelines
├── RM_5_8_1_COVERAGE_REPORT.md     # Coverage analysis
└── RM_5_8_1_EXECUTION_REPORT.md    # Execution summary
```

### Design Principles

1. **Deterministic**: Every case has fixed expected output; no randomness
2. **Versioned**: Corpus v1.0.0 baselined; future versions in v1.1.0/ directories
3. **Human Reviewable**: All JSON cases readable without tools; notes explain reasoning
---

## Benchmark Case Format

### Unified JSON Schema

All 150 cases use identical structure:

```json
{
  "benchmark_id": "CH-EASY-0001",
  "extractor": "character",
  "difficulty": "easy",
  "source_text": "...",
  "expected_entities": [...],
  "expected_confidence": "high",
  "tags": [...],
  "notes": "..."
}
```

### Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| benchmark_id | string | `^(CH\|GL\|SC\|NA\|ST)-(EASY\|MEDIUM\|HARD)-\\d{4}$` | Unique ID: extractor prefix + difficulty + 4-digit sequence |
| extractor | string | enum: character, glossary, scene, narrative, style | Target extractor |
| difficulty | string | enum: easy, medium, hard | Difficulty tier |
| source_text | string | minLength: 1 | Input text for extraction |
| expected_entities | array | minItems: 1 | Expected extraction results |
| expected_confidence | string | enum: high, medium, low | Expected confidence level |
| tags | array | string[] | Scenario tags for coverage tracking |
| notes | string | - | Human-readable design rationale |

### Entity Structure (Per Extractor)

Each extractor's expected_entities contains objects matching that extractor's entity schema:

- **Character**: id, type, name, aliases, attributes, relationships, appearances
- **Glossary**: id, type, term, definition, translation, context, category, variants
- **Scene**: id, type, location, atmosphere, sensory_details, time_of_day, significance
- **Narrative**: id, type, plot_point, arc, tension_level, pacing, foreshadowing
- **Style**: id, type, tone, literary_devices, sentence_patterns, vocabulary_level, rhythm
---

## Difficulty Tier Design

### Easy (10 cases per extractor)
- Information explicitly stated in source text
- Direct descriptions, clear definitions, obvious transitions
- Expected confidence: high
- Precision target: ≥ 0.95, Recall target: ≥ 0.90

### Medium (10 cases per extractor)
- Information requires inference from context
- Implicit relationships, contextual term usage, scene continuity
- Expected confidence: medium
- Precision target: ≥ 0.80, Recall target: ≥ 0.75

### Hard (10 cases per extractor)
- Ambiguous, multi-hop reasoning, contradictory information
- Same-name disambiguation, polysemy, non-linear narrative
- Expected confidence: low
- Precision target: ≥ 0.65, Recall target: ≥ 0.60
---

## Coverage Requirements

### Character Extractor (30 cases)
| Tag | Difficulty | Cases |
|-----|------------|-------|
| first_appearance | easy | 2 |
| explicit_description | easy | 3 |
| explicit_relationship | easy | 2 |
| title_alias | easy | 2 |
| multi_alias | easy | 1 |
| pronoun_reference | medium | 2 |
| implicit_comparison | medium | 1 |
| action_based_inference | medium | 2 |
| relationship_inference | medium | 2 |
| backstory_revelation | medium | 1 |
| cross_chapter_reference | hard | 1 |
| same_name_disambiguation | hard | 2 |
| dual_persona | hard | 1 |
| identity_convergence | hard | 1 |
| temporal_paradox | hard | 1 |
| generational_mirror | hard | 1 |
| long_term_plot | hard | 1 |
| character_arc_completion | hard | 1 |
| meta_narrative | hard | 1 |

### Glossary Extractor (30 cases)
| Tag | Difficulty | Cases |
|-----|------------|-------|
| explicit_definition | easy | 10 |
| contextual_usage | medium | 5 |
| value_inference | medium | 2 |
| function_inference | medium | 2 |
| pair_terms | medium | 1 |
| polysemy | hard | 1 |
| pun_wordplay | hard | 1 |
| forbidden_form | hard | 1 |
| context_override | hard | 1 |
| name_vs_reality | hard | 1 |
| implicit_fourth_realm | hard | 1 |
| metaphorical_definition | hard | 1 |
| redefinition | hard | 1 |
| acrostic_puzzle | hard | 1 |
| system_level_mapping | hard | 1 |

### Scene Extractor (30 cases)
| Tag | Difficulty | Cases |
|-----|------------|-------|
| new_scene | easy | 10 |
| scene_continuation | medium | 2 |
| time_progression | medium | 1 |
| location_switch | medium | 2 |
| transition_aftermath | medium | 1 |
| night_scene | medium | 1 |
| barrier_passage | medium | 1 |
| trap_environment | medium | 1 |
| time_jump | medium | 1 |
| ensemble_scene | medium | 1 |
| post_climax | medium | 1 |
| dreamscape | medium | 1 |
| subjective_reality | hard | 1 |
| temporal_superposition | hard | 1 |
| time_dilation | hard | 1 |
| time_river_metaphor | hard | 1 |
| multi_location_superposition | hard | 1 |
| dream_reality_bleed | hard | 1 |
| world_rewriting | hard | 1 |
| reader_as_writer | hard | 1 |
| fixed_scene_variable_details | hard | 1 |
| concept_elimination | hard | 1 |

### Narrative Extractor (30 cases)
| Tag | Difficulty | Cases |
|-----|------------|-------|
| plot_point | easy | 10 |
| hidden_clue | medium | 1 |
| betrayal_twist | medium | 1 |
| deadline_resolution | medium | 1 |
| forbidden_art_reveal | medium | 1 |
| ensemble_climax | medium | 1 |
| posthumous_guidance | medium | 1 |
| double_agent_reveal | medium | 1 |
| final_battle_twist | medium | 1 |
| time_loop_reveal | medium | 1 |
| meta_fiction_awakening | medium | 1 |
| handwriting_as_narrative | hard | 1 |
| temporal_superposition | hard | 1 |
| concept_to_law | hard | 1 |
| acrostic_decoding | hard | 1 |
| cycle_log_revelation | hard | 1 |
| dream_reality_bleed | hard | 1 |
| world_rewriting | hard | 1 |
| system_level_isomorphism | hard | 1 |
| differential_storage | hard | 1 |
| concept_suicide | hard | 1 |

### Style Extractor (30 cases)
| Tag | Difficulty | Cases |
|-----|------------|-------|
| author_sentence_pattern | easy | 5 |
| dialogue_rhythm | easy | 1 |
| first_person | easy | 1 |
| standard_punctuation | easy | 1 |
| general_specific_general | easy | 1 |
| short_sentences | easy | 1 |
| glossing_technique | easy | 1 |
| cliffhanger | easy | 1 |
| concrete_metaphor | easy | 1 |
| explicit_time_markers | easy | 1 |
| honorifics | easy | 1 |
| circular_structure | easy | 1 |
| long_sentence | medium | 1 |
| dialogue_rhythm | medium | 1 |
| rhetorical_device | medium | 3 |
| narrative_distance | medium | 1 |
| pun_permeation | medium | 1 |
| plain_description | medium | 1 |
| fragmented_flashback | medium | 1 |
| honorifics | medium | 1 |
| code_literature_isomorphism | medium | 1 |
| participatory_narrative | medium | 1 |
| calligraphy_as_narrative | hard | 1 |
| temporal_superposition | hard | 1 |
| triple_textual_voices | hard | 1 |
| cross_system_acrostic | hard | 1 |
| text_as_data_structure | hard | 1 |
| dream_modality_shift | hard | 1 |
| world_rewriting_as_text_rewriting | hard | 1 |
| system_level_isomorphism | hard | 1 |
| git_diff_metaphor | hard | 1 |
| concept_suicide | hard | 1 |
---

## Manifest Specification

### benchmark_manifest.json Structure

```json
{
  "corpus_version": "1.0.0",
  "created_at": "2026-08-04T00:00:00Z",
  "total_cases": 150,
  "extractor_counts": {...},
  "difficulty_counts": {...},
  "extractor_difficulty_matrix": {...},
  "benchmark_ids": [...],
  "checksum": "sha256:...",
  "schema_version": "1.0.0",
  "specification_doc": "RM_5_8_0_GOLDEN_DATASET_SPEC.md"
}
```

### Checksum Computation

- SHA-256 of all case files concatenated in benchmark_id order
- Stored in manifest for integrity verification
- Recomputed on any corpus modification

---

## Validation Rules

### Automated Checks
1. All JSON files validate against `benchmark_case_schema.json`
2. All `benchmark_id` values unique across corpus
3. No duplicate `source_text` across cases
4. `difficulty` ∈ {easy, medium, hard}
5. `extractor` ∈ {character, glossary, scene, narrative, style}
6. `expected_confidence` ∈ {high, medium, low}
7. `expected_entities` array non-empty
8. Manifest counts match actual file counts
9. Manifest checksum matches computed checksum

### Coverage Checks
1. Each required tag appears in at least 1 case per extractor
2. Each extractor has exactly 10 cases per difficulty
3. Total cases = 150 (30 × 5)

---

## Acceptance Criteria

- [x] Benchmark Corpus Framework complete (directories, schema, manifest)
- [x] Benchmark Case Schema complete (benchmarks/spec/benchmark_case_schema.json)
- [x] Manifest complete (benchmarks/spec/benchmark_manifest.json)
- [x] Five Extractor Corpus established (150 cases in benchmarks/golden/)
- [x] Coverage Report complete (RM_5_8_1_COVERAGE_REPORT.md)
- [x] Runtime Modified = 0 (no changes to core/, lts/, runtime_api/)
- [x] Provider Requests = 0 (no API calls)
- [x] Network Requests = 0 (no outbound connections)
- [x] `git diff --check` PASS (whitespace/line-ending compliance)
4. **Provider Independent**: No API calls; pure ground truth data
5. **Benchmark Ready**: Schema compatible with future Benchmark Runner