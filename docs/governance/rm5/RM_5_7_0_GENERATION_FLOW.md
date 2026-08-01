# RM-5.7.0 Knowledge Generation Flow

**Baseline**: RM-5.7.0 Architecture Baseline  
**Version**: RM-5.7.0  
**Status**: Process Governance  
**Created**: 2026-08-02  
**Purpose**: Detailed generation pipeline flows — extraction, validation, compilation, and quality gates for each knowledge domain.

---

## 1. Generation Pipeline Overview

### 1.1 Pipeline Stages

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  1. SOURCE  │──►│  2. EXTRACT │──►│  3. VALIDATE│──►│  4. REVIEW  │──►│  5. COMPILE │
│  INGESTION  │   │  AGENTS     │   │  ENGINE     │   │  & APPROVE  │   │  ARTIFACTS  │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
      │               │               │               │               │
      ▼               ▼               ▼               ▼               ▼
  Corpus         Candidates      Validated       Approved      Versioned
  Collection     (Raw JSON)      Candidates      Candidates    Artifacts
```

### 1.2 Stage Characteristics

---

## 2. Stage 1: Source Ingestion

### 2.1 Input Sources

| Source Type | Format | Location | Processing |
|-------------|--------|----------|------------|
| Novel Text | `.txt` / `.md` | `data/source/{volume}/` | UTF-8 normalization, chapter splitting |
| Existing Glossary | `glossary.txt` / `glossary.json` | `data/` / `memory/` | Schema migration to v1.0.0 |
| Character Memory | `character_memory.json` | `memory/` | Schema migration to v1.0.0 |
| Style Guides | `.md` | `docs/style/` | Parse into ToneProfile/RegisterRule |
| Translation Samples | `.jsonl` | `artifacts/samples/` | Extract style patterns |

### 2.2 Corpus Normalization

```python
def normalize_corpus(source_dir: Path) -> Corpus:
    """Normalize source text for extraction agents."""
    return Corpus(
        volumes=[
            Volume(
                volume_id=vol_num,
                chapters=split_chapters(read_text(file)),
                metadata=extract_metadata(file)
            )
            for vol_num, file in enumerate(sorted(source_dir.glob("*.txt")), 1)
        ]
    )
```

**Output**: `Corpus` object with volumes → chapters → paragraphs structure.

---

## 3. Stage 2: Extraction Agents

### 3.1 Agent Architecture

Each extraction agent follows a common pattern:

```python
class ExtractionAgent(Protocol):
    def extract(self, corpus: Corpus, context: ExtractionContext) -> list[CandidateEntity]: ...
    def get_prompt_template(self) -> str: ...
    def get_model_config(self) -> ModelConfig: ...

class ExtractionContext:
    existing_entities: dict[str, list[BaseEntity]]  # Prior knowledge for incremental extraction
    domain_config: DomainConfig  # Domain-specific parameters
    few_shot_examples: list[Example]  # Curated examples for prompt
```

### 3.2 GlossaryExtractor

| Parameter | Value |
|-----------|-------|
| **Model** | NVIDIA llama-3.3-70b-instruct (offline batch) |
| **Temperature** | 0.1 (deterministic extraction) |
| **Max Tokens** | 4096 |
| **Prompt Strategy** | Chapter-by-chapter with sliding context window |
| **Few-Shot** | 5 curated examples per domain_tag |

**Extraction Prompt Template**:
```
Extract glossary terms from the following {domain_tag} novel chapter.

EXISTING GLOSSARY (do not duplicate):
{existing_terms}

CHAPTER TEXT:
{chapter_text}

OUTPUT FORMAT: JSON array of term candidates with fields:
- source_term (original)
- canonical (target language authoritative form)
- domain_tags (array)
- part_of_speech (enum)
- context_rules (conditional translations)
- aliases (variants)
### 3.4 NarrativeExtractor

| Parameter | Value |
|-----------|-------|
| **Model** | NVIDIA llama-3.3-70b-instruct (offline batch) |
| **Temperature** | 0.2 (slightly more creative for plot analysis) |
| **Max Tokens** | 8192 |
| **Prompt Strategy** | Volume-level with structural analysis |
| **Few-Shot** | 2 curated examples per plot type |

**Extraction Focus**:
- Scene boundaries (location, time, participants)
- Plot points (type, description, timeline position)
- World rules (cultivation systems, political structures)
- Character milestones (breakthroughs, revelations)

**Output**: `list[NarrativeCandidate]` with `status="draft"`.

### 3.5 StyleExtractor

| Parameter | Value |
|-----------|-------|
| **Method** | Rule-based + LLM hybrid |
| **Temperature** | 0.0 (fully deterministic) |
| **Input** | Translation samples + style guides |
| **Output** | ToneProfile, RegisterRule, FormattingConvention |

**Extraction Process**:
1. **Rule-based**: Parse style guide markdown for explicit rules
2. **LLM Analysis**: Analyze translation samples for implicit patterns
3. **Synthesis**: Merge into dimension scores (formality, emotionality, etc.)
4. **Validation**: Cross-check against style guide requirements

---

## 4. Stage 3: Validation Engine

### 4.1 Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    VALIDATION ENGINE                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Schema Validation    │ JSON Schema Draft 2020-12  │
│  Layer 2: Business Rules       │ Domain-specific constraints│
│  Layer 3: Cross-References     │ UUID resolution, integrity │
│  Layer 4: Confidence Threshold │ Per-domain minimum scores  │
│  Layer 5: Deduplication        │ Canonical uniqueness       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Schema Validation

- **Tool**: `jsonschema` Python library (Draft 2020-12)
- **Scope**: Every candidate entity against its domain schema
- **Failure Action**: Reject candidate; log validation errors
- **Performance**: < 100ms per 1000 entities

### 4.3 Business Rule Validation

| Domain | Rules | Implementation |
|--------|-------|----------------|
| Glossary | GL-001 to GL-005 | Python validators in `validators/glossary.py` |
| Character | CH-001 to CH-005 | Python validators in `validators/character.py` |
| Narrative | NR-001 to NR-004 | Python validators in `validators/narrative.py` |
| Style | ST-001 to ST-003 | Python validators in `validators/style.py` |

### 4.4 Cross-Reference Validation

```python
def validate_cross_references(entities: dict[str, list[BaseEntity]]) -> ValidationResult:
    """Validate all UUID references resolve."""
    all_ids = {e.id for domain_entities in entities.values() for e in domain_entities}
    
    errors = []
    for domain, domain_entities in entities.items():
        for entity in domain_entities:
            for ref_id in entity.get_references():
                if ref_id not in all_ids:
---

## 5. Stage 4: Review & Approval

### 5.1 Review Workflow

```
Validated Candidates
        │
        ▼
┌───────────────────┐
│  Auto-Approve     │  ──► confidence ≥ threshold + no rule warnings
│  (High Confidence)│
└───────────────────┘
        │
        ▼ (remaining)
┌───────────────────┐
│  Human Review     │  ──► Translator/Editor review in review UI
│  Queue            │
└───────────────────┘
        │
        ├──► APPROVE ──► status = "approved"
        ├──► REVISE  ──► back to extraction with feedback
        └──► REJECT  ──► status = "deprecated"
```

### 5.2 Review Criteria

| Criterion | Glossary | Character | Narrative | Style |
|-----------|----------|-----------|-----------|-------|
| Translation Accuracy | ✓ | ✓ | N/A | ✓ |
| Consistency | ✓ | ✓ | ✓ | ✓ |
| Completeness | ✓ | ✓ | ✓ | ✓ |
| Canonical Form | ✓ | ✓ | N/A | N/A |
| Evidence Quality | N/A | ✓ | ✓ | ✓ |
---

## 6. Stage 5: Compilation & Artifacts

### 6.1 Compilation Process

```python
def compile_artifacts(approved_entities: dict[str, list[BaseEntity]]) -> CompilationResult:
    """Compile approved entities into versioned artifacts."""
    
    artifacts = {}
    for domain, entities in approved_entities.items():
        # Sort for deterministic output
        sorted_entities = sorted(entities, key=lambda e: e.id)
        
        # Write domain artifact
        artifact_path = Path(f"memory/knowledge/{domain}.json")
        artifact_path.write_text(
            json.dumps([e.to_dict() for e in sorted_entities], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Compute checksum
        checksum = sha256(artifact_path.read_bytes()).hexdigest()
        artifacts[domain] = ArtifactInfo(
            domain=domain,
            path=artifact_path,
            entity_count=len(entities),
            checksum_sha256=checksum,
            size_bytes=artifact_path.stat().st_size
        )
    
    # Generate manifest
    manifest = KnowledgeManifest(
        manifest_version="1.0.0",
        generated_at=datetime.utcnow().isoformat() + "Z",
        generator_version="rm5.7.0",
        schema_versions=get_current_schema_versions(),
        domains=list(artifacts.values()),
        validation_summary=run_final_validation(approved_entities)
    )
    
    manifest_path = Path("memory/knowledge/manifest.json")
    manifest_path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    
    return CompilationResult(artifacts=artifacts, manifest=manifest)
```

### 6.2 Artifact Layout

```
memory/knowledge/
├── manifest.json              # KnowledgeManifest
├── glossary.json              # list[GlossaryTerm]
├── character.json             # list[Character]
├── narrative.json             # list[Scene | PlotPoint | Timeline | WorldRule]
└── style.json                 # list[ToneProfile | RegisterRule | FormattingConvention]
```

### 6.3 Manifest Example

```json
{
  "manifest_version": "1.0.0",
  "generated_at": "2026-08-02T10:30:00Z",
  "generator_version": "rm5.7.0",
  "schema_versions": {
    "base": "1.0.0",
    "glossary": "1.0.0",
    "character": "1.0.0",
    "narrative": "1.0.0",
    "style": "1.0.0"
  },
  "domains": [
    {
      "domain": "glossary",
      "artifact_path": "memory/knowledge/glossary.json",
      "entity_count": 1247,
      "checksum_sha256": "a1b2c3d4e5f6...",
      "size_bytes": 452312
    },
    {
      "domain": "character",
      "artifact_path": "memory/knowledge/character.json",
      "entity_count": 89,
      "checksum_sha256": "f6e5d4c3b2a1...",
      "size_bytes": 128456
    }
  ],
  "validation_summary": {
    "schema_valid": true,
---

## 7. Incremental Generation

### 7.1 Incremental Mode

For subsequent volumes in a series:

```python
def incremental_generation(
    new_corpus: Corpus,
    existing_manifest: KnowledgeManifest
) -> CompilationResult:
    """Generate knowledge for new volume only, merge with existing."""
    
    # Load existing approved entities
    existing = load_artifacts(existing_manifest)
    
    # Extract only new candidates
    new_candidates = extract_agents.run(new_corpus, context=ExtractionContext(
        existing_entities=existing
    ))
    
    # Validate & review (same pipeline)
    validated = validate(new_candidates)
    approved = review(validated)
    
    # Merge: new entities + existing (with updates for evolved characters/terms)
    merged = merge_entities(existing, approved)
    
    return compile_artifacts(merged)
```

### 7.2 Merge Strategies

| Entity Type | Merge Strategy |
|-------------|----------------|
| GlossaryTerm | New terms added; existing updated if higher confidence |
| Character | Traits/relationships merged; aliases consolidated |
| Narrative | New scenes/plot points appended; world rules updated |
| Style | Profiles/rules replaced if version bumped |

---

## 8. Quality Gates

### 8.1 Gate Definitions

| Gate | Stage | Criteria | Blocking |
|------|-------|----------|----------|
| Schema Gate | Post-Validation | 100% schema valid | Yes |
| Cross-Ref Gate | Post-Validation | 0 unresolved references | Yes |
| Confidence Gate | Post-Validation | All entities ≥ domain threshold | Yes |
| Review Gate | Post-Review | 100% candidates reviewed | Yes |
| Manifest Gate | Post-Compile | Manifest valid + checksums match | Yes |

### 8.2 Gate Enforcement

```python
class QualityGate:
    def __init__(self, name: str, criteria: Callable[[], bool], blocking: bool):
        self.name = name
        self.criteria = criteria
        self.blocking = blocking
    
    def evaluate(self, context: PipelineContext) -> GateResult:
        passed = self.criteria(context)
        return GateResult(
            gate=self.name,
            passed=passed,
            blocking=self.blocking,
            timestamp=datetime.utcnow()
        )
```

---

## 9. Error Handling & Recovery

### 9.1 Failure Modes

| Failure Point | Recovery Strategy |
|---------------|-------------------|
| Extraction timeout | Retry with reduced context; fallback to rule-based |
| Schema validation error | Auto-fix common issues; flag for manual review |
| Cross-ref unresolved | Search for near-matches; create placeholder |
| Review deadlock | Escalate to lead translator; time-box decision |
| Compilation checksum mismatch | Re-compile from source; verify disk integrity |

### 9.2 Checkpointing

- Every stage writes intermediate state to `artifacts/knowledge_gen/checkpoints/`
- Resume capability: `ntpe_knowledge_gen.py --resume-from validation`
- Atomic artifact writes (temp file + rename)

---

## 10. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Full generation (10 volumes) | < 4 hours | Wall clock |
| Extraction per volume | < 30 min | LLM API time |
| Validation (10k entities) | < 5 min | CPU time |
| Compilation | < 2 min | Wall clock |
| Artifact load time (runtime) | < 500 ms | Cold start |

---

## 11. References

- RM-5.7.0 Architecture Baseline: `RM_5_7_0_KNOWLEDGE_GENERATION_ARCHITECTURE.md`
- RM-5.7.0 Schema Design: `RM_5_7_0_KNOWLEDGE_SCHEMA_DESIGN.md`
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/
    "cross_refs_valid": true,
    "business_rules_passed": 1336,
    "business_rules_failed": 0,
    "warnings": 3
  }
}
```

### 5.3 Review Tools

- **Review UI**: Web-based (future) or CLI `ntpe_knowledge_review.py`
- **Diff View**: Side-by-side candidate vs existing approved
- **Bulk Actions**: Approve all high-confidence, flag conflicts
- **Audit Trail**: Every decision logged with reviewer, timestamp, rationale
                    errors.append(f"Unresolved reference: {ref_id} from {entity.id}")
    
    return ValidationResult(valid=len(errors)==0, errors=errors)
```

### 4.5 Confidence Thresholds

| Domain | Draft → Validated | Validated → Approved |
|--------|-------------------|----------------------|
| Glossary | ≥ 0.6 | ≥ 0.8 |
| Character | ≥ 0.6 | ≥ 0.85 |
| Narrative | ≥ 0.5 | ≥ 0.75 |
| Style | ≥ 0.7 | ≥ 0.9 |

### 4.6 Deduplication

- **Glossary**: Merge by `(canonical, domain_tags)` — keep highest confidence
- **Character**: Merge by `name` (fuzzy match threshold 0.9) — consolidate aliases/traits
- **Narrative**: Merge by `scene_id` / `plot_id` — deterministic IDs prevent duplicates
- **Style**: Merge by `profile_id` / `rule_id` / `convention_id` — deterministic IDs
- confidence (0.0-1.0)
```

**Output**: `list[GlossaryTermCandidate]` with `status="draft"`.

### 3.3 CharacterExtractor

| Parameter | Value |
|-----------|-------|
| **Model** | NVIDIA llama-3.3-70b-instruct (offline batch) |
| **Temperature** | 0.1 |
| **Max Tokens** | 4096 |
| **Prompt Strategy** | Full-volume analysis with character tracking |
| **Few-Shot** | 3 curated examples per role type |

**Extraction Focus**:
- Name variants (aliases, titles, honorifics)
- Personality traits with evidence citations
- Relationships with strength/direction
- Cultivation realm / power system progression
- Speech patterns and verbal tics

**Output**: `list[CharacterCandidate]` with `status="draft"`.
| Stage | Automation | Human Involvement | Output | Duration Target |
|-------|------------|-------------------|--------|-----------------|
| Source Ingestion | 100% | None | Normalized corpus | < 5 min |
| Extraction | 80% (LLM) | Prompt tuning | Candidate entities | 30-60 min/volume |
| Validation | 100% | Rule authoring | Validated entities | < 10 min |
| Review & Approve | 0% | Full review | Approved entities | Variable |
| Compilation | 100% | Config | Artifacts + Manifest | < 5 min |