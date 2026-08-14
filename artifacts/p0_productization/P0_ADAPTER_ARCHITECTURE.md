# P0 Adapter Architecture Definition

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Allowed Adapters (P0 Scope)

Per Stage 0 spec, only these adapters are permitted:

| Adapter | Responsibility | New/Modify |
|---------|---------------|------------|
| `CanonicalBookIntakeAdapter` | Bridge EPUB extraction → Book Intake | NEW |
| `EpubExtractionBoundary` | EPUB → TXT extraction | NEW |
| `ProductionSubmissionAdapter` | Reader Web App → Production CLI | NEW |
| `ProgressCheckpointAdapter` | Reader Web App → LTS resume/progress JSON | NEW |
| `Rm8DeliveryAdapter` | Reader Web App → RM-8.3/8.4 delivery | NEW |

---

## Forbidden in P0

| Forbidden Component | Reason |
|---------------------|--------|
| `NewTranslationRuntime` | Reuse existing `TranslationRuntime` + `lts/txt_translation_runtime` |
| `NewLauncher` | Reuse `ntpe_production_translate.py` |
| `NewResumeEngine` | Reuse LTS `*_resume_state.json` + `*_live_progress.json` |
| `NewChunkEngine` | Reuse `split_text()` + `translate_package_with_retry()` |
| `NewProviderAdapter` | Reuse `RuntimeProviderAdapter` + `AIProvider` |
| `NewQualityEngine` | Reuse Quality V5 + Runtime QA + Discipline |

**Unless** next stage audit explicitly proves necessity.

---

## Adapter Specifications

### 1. CanonicalBookIntakeAdapter

**Purpose**: Normalize any input (TXT, extracted EPUB) → `BookIntakeResult`

**Input**: 
- `source_path: Path` (TXT or extracted TXT from EPUB)
- `source_identity: SourceIdentity` (original file hash, metadata)

**Output**: `BookIntakeResult` (from `core.book_intake`)

**Implementation**:
```python
class CanonicalBookIntakeAdapter:
    def __init__(self):
        self.processor = BookIntakeProcessor()  # Existing frozen component
    
    def process(self, source_path: Path, source_identity: SourceIdentity) -> BookIntakeResult:
        result = self.processor.process(source_path)
        # Attach source identity for provenance
        return result
```

**Reuses**: `core.book_intake.BookIntakeProcessor` (frozen, Stage 2.8)

---

### 2. EpubExtractionBoundary

**Purpose**: EPUB → Extracted TXT + Extraction Manifest

**Input**: `epub_path: Path`

**Output**: `EpubExtractionResult`
```python
@dataclass(frozen=True)
class EpubExtractionResult:
    source_path: Path
    original_hash: str           # SHA256 of EPUB
    extracted_text: str          # Canonical TXT body
    extracted_hash: str          # SHA256 of extracted text
    metadata: EpubMetadata       # DC metadata
    chapter_map: list[ChapterBoundary]
    extraction_manifest: ExtractionManifest
    status: str
    warnings: tuple[str, ...]
```

**Implementation**: NEW — uses `ebooklib` or similar, no translation

**Contract**: See `P0_EPUB_INPUT_REQUIREMENTS.md`

---

### 3. ProductionSubmissionAdapter

**Purpose**: Reader Web App submission → `ntpe_production_translate.py` CLI

**Input**: 
- `job_request: TranslationJobRequest` (input file, options, profile, etc.)

**Output**: `SubmissionResult`
```python
@dataclass(frozen=True)
class SubmissionResult:
    job_id: str
    status: str  # "submitted" | "running" | "completed" | "failed"
    cli_command: list[str]  # For audit/replay
    output_dir: Path
```

**Implementation**: 
- Builds CLI argv for `ntpe_production_translate.py txt`
- Spawns subprocess with proper env vars (`NTPE_RUNTIME_PIPELINE=runtime`)
- Returns job_id for tracking

**Reuses**: Existing production CLI — no new translation logic

---

### 4. ProgressCheckpointAdapter

**Purpose**: Reader Web App ↔ LTS Resume/Progress JSON

**Reads**:
- `{output_dir}/{stem}_resume_state.json` — chunk completion status
- `{output_dir}/{stem}_live_progress.json` — real-time progress

**Writes**: 
- Nothing (read-only for progress UI)
- Optionally: cancellation signal via marker file

**Interface**:
```python
class ProgressCheckpointAdapter:
    def get_resume_state(self, output_dir: Path, stem: str) -> ResumeState:
        # Parses *_resume_state.json
    
    def get_live_progress(self, output_dir: Path, stem: str) -> LiveProgress:
        # Parses *_live_progress.json
    
    def get_chunk_progress(self, resume_state: ResumeState) -> ChunkProgress:
        # Computes: completed, failed, pending, total
```

**Reuses**: Existing LTS JSON format (frozen)

---

### 5. Rm8DeliveryAdapter

**Purpose**: Reader Web App → RM-8.3 Delivery + RM-8.4 EPUB

**Input**: 
- `delivery_request: DeliveryRequest` (formats: txt, epub, pdf)

**Output**: `DeliveryResult` (from `core.translation_release.delivery_pipeline`)

**Implementation**:
- Reads `quality_delivery_v83` and `quality_delivery_formats_v83` from job options
- Calls `run_delivery_pipeline()` with assembled text + chunk records
- Returns `DeliveryResult` with all artifact paths

**Reuses**: `core.translation_release.delivery_pipeline.run_delivery_pipeline()`

---

## Adapter Dependency Graph

```
Reader Web App (web/reader/app/)
         |
         v
��─────────────────────────────────────��
│  ProductionSubmissionAdapter        │  ← Submits job to CLI
��─────────────────────────────────────��
         |
         v
��─────────────────────────────────────��
│  ntpe_production_translate.py       │  ← Existing production CLI
│  (txt command)                      │
��─────────────────────────────────────��
         |
         v
��─────────────────────────────────────��
│  TranslationRuntime                 │  ← Existing facade
��─────────────────────────────────────��
         |
         v
��─────────────────────────────────────��
│  lts/txt_translation_runtime        │  ← Existing LTS runtime
│  translate_txt()                    │
��─────────────────────────────────────��
         |
    +----+----+
    |         |
    v         v
��─────────�� ��─────────────────────��
│ Book    │ │ RM-8.3 Delivery     │
│ Intake  │ │ Pipeline            │
│ (frozen)│ │ (feature-gated)     │
��─────────�� └─────────────────────��
    |         |
    v         v
��─────────�� ��─────────────────────��
│ Canon   │ │ EPUB Packager       │
│ TXT     │ │ (optional, RM-8.4)  │
��─────────�� └─────────────────────��
```

---

## Adapter Implementation Location

| Adapter | Proposed Location |
|---------|-------------------|
| `CanonicalBookIntakeAdapter` | `core/adapters/canonical_book_intake_adapter.py` |
| `EpubExtractionBoundary` | `core/adapters/epub_extraction_boundary.py` |
| `ProductionSubmissionAdapter` | `core/adapters/production_submission_adapter.py` |
| `ProgressCheckpointAdapter` | `core/adapters/progress_checkpoint_adapter.py` |
| `Rm8DeliveryAdapter` | `core/adapters/rm8_delivery_adapter.py` |

**New directory**: `core/adapters/` (governance: core/ is runtime-owned)

---

## Integration Points (No New Abstractions)

| Integration | Existing Component | Adapter Role |
|-------------|-------------------|--------------|
| CLI submission | `ntpe_production_translate.py` | `ProductionSubmissionAdapter` builds argv, spawns process |
| Progress polling | `*_resume_state.json`, `*_live_progress.json` | `ProgressCheckpointAdapter` parses JSON |
| Delivery trigger | `options.quality_delivery_v83` | `Rm8DeliveryAdapter` passes flags to runtime |
| EPUB packaging | `pack_epub()` via delivery pipeline | `Rm8DeliveryAdapter` reads `epub_path` from `DeliveryResult` |
| Book intake | `BookIntakeProcessor` | `CanonicalBookIntakeAdapter` wraps processor |

---

## Key Principle

> **Adapters wire existing contracts — they do not create new runtime behavior.**

Each adapter is a thin translation layer between:
- Reader Web App domain model
- Existing NTPE production contracts (CLI, JSON, Python APIs)

No new:
- Translation engines
- Chunking logic
- Retry policies
- Provider adapters
- Quality gates
- Resume mechanisms