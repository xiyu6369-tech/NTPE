# Difficulty Definition for Knowledge Benchmark Corpus

## Overview

This document defines the three difficulty tiers used in the NTPE Knowledge Benchmark Corpus. Each tier represents increasing complexity in the extraction task, requiring progressively more sophisticated reasoning capabilities from the Knowledge Extractors.

---

## Tier 1: Easy (直觀顯性)

### Definition
Information is **explicitly stated** in the source text with clear, unambiguous markers. The extractor needs only to identify and extract directly stated facts.

### Characteristics
- Direct character descriptions with explicit names
- Explicit term definitions (「XXX 是指...」）
- Clearly marked scene transitions (「場景轉至...」）
- Explicit plot point statements (「這是轉折點...」）
- Obvious stylistic markers (first-person, clear dialogue tags)

### Example Scenarios
| Extractor | Easy Example |
|-----------|--------------|
| Character | "林小滿，二十五歲，是本故事的主角。" |
| Glossary | "修煉者（Cultivator）：指修習靈氣之人。" |
| Scene | "場景轉至青雲門大殿，晨光透過窗棂灑在青石地面上。" |
| Narrative | "這是故事的開端，主角踏上修仙之路。" |
| Style | "作者使用第一人稱敘事，語氣溫和細膩。" |

### Expected Extractor Performance
- **Precision Target**: ≥ 0.95
- **Recall Target**: ≥ 0.90
- **Confidence**: High confidence expected
---

## Tier 2: Medium (隱性推理)

### Definition
Information is **implicitly conveyed** and requires **inference** from context. The extractor must combine multiple textual clues to derive the correct extraction.

### Characteristics
- Character relationships implied through dialogue/actions
- Terms used in context without explicit definition
- Scene continuity requiring temporal/spatial reasoning
- Plot points that connect across paragraphs/chapters
- Style patterns requiring analysis of multiple sentences

### Example Scenarios
| Extractor | Medium Example |
|-----------|----------------|
| Character | Two characters discuss "師兄" without naming him; extractor must infer identity from context |
| Glossary | "丹藥入喉化作暖流" — term "丹藥" undefined but context implies medicinal pill |
| Scene | Same location referenced across paragraphs with time progression cues only |
| Narrative | Cause-effect chain spanning multiple paragraphs: earlier action leads to later consequence |
| Style | Recurring sentence structure pattern detectable across 3+ paragraphs |

### Expected Extractor Performance
- **Precision Target**: ≥ 0.80
- **Recall Target**: ≥ 0.75
- **Confidence**: Medium confidence expected

---

## Tier 3: Hard (模糊多跳)

### Definition
Information is **ambiguous, contradictory, or requires multi-hop reasoning** across distant text segments. The extractor must resolve conflicts, track long-range dependencies, and handle edge cases.

### Characteristics
- Same name refers to different characters (disambiguation required)
- Terms with multiple meanings requiring context disambiguation
- Non-linear narrative (flashbacks, parallel timelines)
- Subtle style markers requiring deep literary analysis
- Contradictory information requiring resolution

### Example Scenarios
| Extractor | Hard Example |
|-----------|--------------|
| Character | "李明" appears in Chapter 1 and Chapter 10 — same person or different? Context suggests different people with same name |
| Glossary | "道" used as "Dao (philosophy)", "path (physical)", and "method (cultivation)" in same chapter |
| Scene | Dream sequence blending memory and present; location shifts without explicit markers |
| Narrative | Flashback within flashback; cause-effect separated by 5+ chapters with unreliable narrator |
| Style | Author mimics different historical styles; irony/sarcasm detectable only through deep context |

### Expected Extractor Performance
- **Precision Target**: ≥ 0.65
- **Recall Target**: ≥ 0.60
- **Confidence**: Low confidence acceptable (extractor should express uncertainty)
---

## Difficulty Assignment Guidelines

### For Corpus Creators

When creating new benchmark cases, assign difficulty based on:

1. **Explicitness**: Is the target information directly stated? → Easy
2. **Inference Steps**: How many logical steps from text to answer?
   - 1 step → Easy/Medium boundary
   - 2-3 steps → Medium
   - 4+ steps or conflicting evidence → Hard
3. **Context Span**: How far apart are relevant clues?
   - Same sentence/paragraph → Easy
   - Same scene/chapter → Medium
   - Cross-chapter / whole novel → Hard
4. **Ambiguity**: Are there competing interpretations?
   - None → Easy
   - Resolvable with local context → Medium
   - Requires global knowledge / subjective judgment → Hard

### Difficulty Tag Reference

Each case must include relevant tags from this taxonomy:

#### Character Tags
- `first_appearance` (Easy)
- `multi_alias` (Medium)
- `pronoun_reference` (Medium)
- `cross_chapter_reference` (Hard)
- `same_name_disambiguation` (Hard)
- `relationship_change` (Hard)

#### Glossary Tags
- `explicit_definition` (Easy)
- `polysemy` (Medium)
- `foreign_term` (Medium)
- `abbreviation` (Medium)
- `context_override` (Hard)
- `forbidden_form` (Hard)

#### Scene Tags
- `new_scene` (Easy)
- `scene_continuation` (Medium)
- `time_jump` (Medium)
- `location_switch` (Medium)
- `character_exit` (Medium)
- `ensemble_scene` (Hard)

#### Narrative Tags
- `plot_point` (Easy)
- `timeline` (Medium)
- `flashback` (Medium)
- `world_rule` (Medium)
- `milestone` (Medium)
- `cause_effect` (Hard)

#### Style Tags
- `author_sentence_pattern` (Easy)
- `long_sentence` (Medium)
- `dialogue_rhythm` (Medium)
- `rhetorical_device` (Medium)
- `narrative_distance` (Hard)
- `honorifics` (Hard)

---

## Validation Rules

1. **Distribution**: Each extractor must have exactly 10 cases per difficulty tier
2. **Tag Coverage**: Each required tag must appear in at least one case per extractor
3. **No Duplication**: No two cases may have identical `source_text` 
4. **ID Format**: Must follow `{PREFIX}-{DIFFICULTY}-{NNNN}` pattern
5. **Confidence Alignment**: Easy→High, Medium→Medium, Hard→Low (with exceptions documented in notes)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-04 | Initial definition for RM-5.8.1 |