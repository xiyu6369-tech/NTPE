# RM-5.7.1 Glossary Extraction Capability Audit

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit  
**Created**: 2026-08-02  
**Purpose**: Audit existing glossary extraction capabilities across all modules to identify gaps for Knowledge Generation Architecture.

---

## 1. Module Inventory

| Module | Path | Type | Status |
|--------|------|------|--------|
| Glossary Builder v1.1.1 | `core/glossary_builder.py` | Extraction + Merge | Active (Offline) |
| Glossary Runtime | `core/glossary.py` | Runtime Loader + Enforcement | Active (Runtime) |
| Knowledge Base Builder | `core/knowledge_base_builder.py` | Integration | Active (Offline) |

---

## 2. Capability Analysis by Module

### 2.1 Glossary Builder v1.1.1 (`glossary_builder.py`)

**Purpose**: Merge multi-volume glossary auto-candidates, apply overrides, export `glossary.json`, `character_alias_index.json`, report & CSV

**Input Sources**:
- `analysis/*_glossary_auto.json` (from Document Analyzer)
- `glossary_override.json` (manual glossary)

| Context rules | ✅ `context_rules` with priority | Basic |
| Confidence scoring | ✅ `confidence_score()` based on count/book_count/locked | Heuristic |
| Character alias index | ✅ `build_character_alias_index()` via CharacterResolver | Integrated |
| Filtering | ✅ MIN_TOTAL_COUNT=2 threshold | Configurable |

**Output Artifacts**:
- `memory/glossary.json` - full glossary database
- `memory/character_alias_index.json` - resolver-compatible alias index
- `memory/glossary.csv` - tabular export
- `memory/glossary_report.txt` - human-readable report

**Gaps**:
- No structured domain tags (only single category classification)
- No part-of-speech tagging
- No evidence citations at segment level (only book-level)
- No semantic relationship modeling between terms
- No term evolution / temporal tracking
- Classification is rule-based only (no LLM semantic understanding)

---

### 2.2 Glossary Runtime (`glossary.py`)

**Purpose**: Runtime glossary loader with term enforcement and output fix

**Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Text file loading | ✅ Loads `data/glossary.txt` (key=value format) |
| Prompt block generation | ✅ `prompt_block()` sorted by length desc |
| Output fix | ✅ `apply_output_fix()` with hardcoded corrections |
| Required term check | ✅ `check_required_terms()` validates enforcement |

**Gaps**:
- Loads from text file, NOT from structured `memory/glossary.json`
- No schema validation
- No domain-aware term selection
- Hardcoded fixes only (not data-driven)
- Runtime-only, no extraction capabilities

---

### 2.3 Knowledge Base Builder (`knowledge_base_builder.py`)

**Purpose**: Integrate character_memory + glossary into unified knowledge base

**Capabilities**:
- Builds alias index from both sources
- Creates locked_index for enforced terms
- Generates prompt_dictionary for translation
- Outputs unified `knowledge_base.json` + `knowledge_base_only.json`

**Gaps**:
- Downstream consumer only (no independent extraction)
- No schema versioning
- No validation beyond JSON structure

---

## 3. Schema Coverage vs RM-5.7.0 Requirements

| RM-5.7.0 Schema Field | Builder v1.1.1 | Runtime | KB Builder | Gap |
|----------------------|----------------|---------|------------|-----|
---

## 4. Extraction Pipeline Gaps

### 4.1 Missing Extraction Stages

| Stage | Current State | Required |
|-------|---------------|----------|
| Source Ingestion | Document Analyzer → `analysis/*_glossary_auto.json` | ✅ Exists |
| Extraction Agents | **None** — Builder only merges pre-extracted candidates | ❌ Need GlossaryExtractor (LLM-based) |
| Validation Engine | Count threshold + rule-based classification only | ❌ Need business rules (GL-001 to GL-005) |
| Review & Approve | Manual override file only | ❌ Need review workflow |
| Compilation | Builder produces glossary.json + alias index | ❌ Need unified artifact per schema |

### 4.2 Missing LLM-Based Extraction

No module performs **LLM-based glossary extraction from source text** with semantic understanding. Classification is purely regex-based.

---

## 5. Identified Gaps Summary

| Gap ID | Category | Description | Severity |
|--------|----------|-------------|----------|
| GLOSS-001 | Schema | No UUID, schema_version, timestamps, source_refs in Builder output | High |
| GLOSS-002 | Schema | Single category only; missing domain_tags, part_of_speech | High |
| GLOSS-003 | Extraction | No LLM-based extraction agent for term semantics | Critical |
| GLOSS-004 | Extraction | No segment-level evidence chain | High |
| GLOSS-005 | Pipeline | No validation engine with business rules (GL-001 to GL-005) | High |
| GLOSS-006 | Pipeline | No review/approval workflow | Medium |
| GLOSS-007 | Runtime | Runtime loader uses text file, not structured artifact | High |
| GLOSS-008 | Coverage | No term relationship modeling (synonyms, antonyms, hypernyms) | Medium |
| GLOSS-009 | Coverage | No temporal term evolution tracking | Medium |

---

## 6. Recommendations

### Immediate (RM-5.7.1 Scope)
1. Document all gaps in this audit
2. Define GlossaryExtractor agent interface
3. Plan migration from text-file runtime to structured artifact

### Future (RM-5.7.2+)
1. **GlossaryExtractor Agent**: LLM-based with domain_tags, POS, context_rules
2. **Unified Schema**: Migrate Builder output to RM-5.7.0 glossary.schema.json
3. **Runtime Switch**: Config flag to load from `memory/knowledge/glossary.json`
4. **Validation Engine**: Implement GL-001 to GL-005

---

## 7. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**
| id (UUID) | ❌ | ❌ | ❌ | **All** |
| schema_version | ❌ | ❌ | ❌ | **All** |
| domain | ❌ | ❌ | ❌ | **All** |
| created_at/updated_at | ❌ | ❌ | ❌ | **All** |
| source_refs | ❌ (book-level only) | ❌ | ❌ | **All** |
| confidence | ✅ (heuristic) | ❌ | ❌ | Runtime, KB |
| status | ❌ (locked/implicit) | ❌ | ❌ | **All** |
| canonical | ✅ (translation) | ❌ (dst only) | ✅ | Runtime |
| source_term | ✅ (source key) | ✅ (src key) | ✅ | — |
| domain_tags | ❌ (single category) | ❌ | ❌ | **All** |
| part_of_speech | ❌ | ❌ | ❌ | **All** |
| context_rules | ✅ (basic) | ❌ | ❌ | Runtime, KB |
| aliases | ✅ (list) | ❌ | ✅ (alias index) | Runtime |
| forbidden_forms | ✅ | ❌ (hardcoded only) | ❌ | Runtime, KB |
| notes | ✅ | ❌ | ❌ | Runtime, KB |
**Extraction Capabilities**:
| Capability | Implementation | Quality |
|------------|----------------|---------|
| Multi-volume merge | ✅ `merge_glossary()` aggregates by term | Good |
| Auto-classification | ✅ `classify_term()` → abbreviation/code/english_term/person_name/unknown | Rule-based |
| Count/statistics | ✅ total_count, book_count per term | Good |
| Manual override | ✅ `apply_override()` with locked translations | Good |
| Alias tracking | ✅ `aliases` list per term | Basic |
| Forbidden forms | ✅ `forbidden_forms` list per term | Basic |
| Context rules | ✅ `git diff --check` relevant to add more content