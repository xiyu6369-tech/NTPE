# RM-5.8.1 — Corpus Creation Guidelines

## Purpose

This document provides guidelines for creating and maintaining the Knowledge Benchmark Corpus. It ensures consistency, quality, and adherence to the design specification.

---

## Case Creation Workflow

### 1. Planning Phase
- Select extractor and difficulty tier
- Choose coverage tag(s) from required tag list
- Design source_text scenario matching tag requirements
- Define expected_entities with complete attribute sets
- Assign appropriate expected_confidence
- Write human-readable notes explaining design rationale

### 2. Writing Phase
- Create JSON file in correct directory: `benchmarks/golden/{extractor}/{difficulty}/{BENCHMARK_ID}.json`
- Follow unified schema exactly
- Ensure benchmark_id follows pattern: `{PREFIX}-{DIFFICULTY}-{NNNN}`
  - Character: CH
  - Glossary: GL
  - Scene: SC
  - Narrative: NA
  - Style: ST

### 3. Validation Phase
- Run JSON schema validation
- Verify benchmark_id uniqueness
- Check tag coverage
- Update manifest.json
- Recompute checksum

### 4. Review Phase
- Human review of case quality
- Confirm difficulty assignment accuracy
- Verify expected_entities completeness
- Check notes clarity

---

## Source Text Guidelines

### Length
- Easy: 50-200 characters
- Medium: 150-400 characters
- Hard: 200-600 characters

### Content Requirements
- Self-contained: understandable without external context
- Representative: reflects actual novel text patterns
- Unambiguous for easy; appropriately ambiguous for medium/hard
- No copyrighted text; original or public domain

### Language
- Traditional Chinese (zh-TW) for source_text
- English translations in glossary entities where applicable

---

## Expected Entities Guidelines

### Completeness
- Include ALL entities that should be extracted from source_text
- Each entity must have all required fields per extractor schema
- Relationships should be bidirectional where applicable

### Accuracy
- Entity IDs unique within case
- Attribute values match source_text exactly or are valid inferences
- Confidence levels aligned with difficulty (Easy→High, Medium→Medium, Hard→Low)

### Tag Assignment
- At least 1 tag per case
- Tags from predefined taxonomy (see difficulty_definition.md)
- Multiple tags allowed for complex cases

---

## Difficulty Calibration

### Easy → High Confidence
- Information directly stated
- Single inference step maximum
- Local context sufficient
- No competing interpretations

### Medium → Medium Confidence
- 2-3 inference steps
- Context span: same scene/chapter
- Resolvable ambiguity with local context
- Implicit relationships/definitions

### Hard → Low Confidence
- 4+ inference steps or conflicting evidence
- Cross-chapter / whole-novel context span
- Genuine ambiguity requiring judgment
- Multi-hop reasoning, disambiguation needed

---

## Manifest Maintenance

### When to Update
- Adding new cases
- Modifying existing cases
- Removing cases
- Schema version changes

### Update Procedure
1. Increment corpus_version (semantic: patch for fixes, minor for additions)
2. Update created_at timestamp
3. Recalculate all counts
4. Regenerate benchmark_ids array
5. Recompute SHA-256 checksum
5. Commit changes with descriptive message

---

## Quality Checklist

Per case:
- [ ] Valid JSON syntax
- [ ] Schema validation passes
- [ ] benchmark_id unique and correctly formatted
- [ ] extractor/difficulty/confidence valid enums
- [ ] source_text non-empty, appropriate length
- [ ] expected_entities ≥ 1, all required fields present
- [ ] tags from taxonomy, relevant to case
- [ ] notes explain design rationale
- [ ] Difficulty matches content complexity

Per batch:
- [ ] All benchmark_ids unique
- [ ] Tag coverage requirements met
- [ ] Difficulty distribution correct (10/10/10 per extractor)
- [ ] Manifest updated and checksum valid
- [ ] No duplicate source_text