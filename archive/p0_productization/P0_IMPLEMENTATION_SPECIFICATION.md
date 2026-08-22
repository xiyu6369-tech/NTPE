# P0 Implementation Specification

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Exact P0 Implementation Scope

| Component | Action | Details |
|-----------|--------|---------|
| **Reader Web App** | **NEW** | `web/reader/app/` — Next.js + TypeScript frontend |
| **CanonicalBookIntakeAdapter** | **NEW** | `core/adapters/canonical_book_intake_adapter.py` — Wraps frozen `BookIntakeProcessor` |
| **EpubExtractionBoundary** | **NEW** | `core/adapters/epub_extraction_boundary.py` — EPUB → TXT extraction |
| **ProductionSubmissionAdapter** | **NEW** | `core/adapters/production_submission_adapter.py` — Submits to `ntpe_production_translate.py` |
| **ProgressCheckpointAdapter** | **NEW** | `core/adapters/progress_checkpoint_adapter.py` — Reads LTS resume/progress JSON |
| **Rm8DeliveryAdapter** | **NEW** | `core/adapters/rm8_delivery_adapter.py` — Triggers RM-8.3/8.4 delivery |
| **Runtime provenance persistence** | **MODIFY** | `lts/txt_translation_runtime.py` — Persist `context_state_metadata` to `chunk_records` |
| **Official CLI** | **MINIMAL MODIFY** | `ntpe_production_translate.py` — Wire `quality_delivery_formats_v83` to options |
| **TranslationRuntime** | **REUSE** | `core/translation_runtime/runtime.py` — No changes |
| **LTS runtime** | **MINIMAL MODIFY** | `lts/txt_translation_runtime.py` — Fix provenance persistence only |
| **Book Intake** | **REUSE** | `core/book_intake/` — Frozen, no changes |
| **RM-8.3** | **REUSE / MINIMAL WIRING** | `core/translation_release/delivery_pipeline.py` — Already works, ensure reachable |
| **RM-8.4** | **REUSE** | `core/translation_release/reader_structure/` — Already works |
| **Desktop GUI** | **QUARANTINE** | `ui/translation_launcher/` — Keep disabled, no changes |
| **web_ui** | **QUARANTINE** | `web_ui/` — Keep as legacy reference, no changes |
| **runtime_api** | **QUARANTINE** | `runtime_api/` — Keep as legacy reference, no changes |

---

## Files Proposed for Modification

### 1. lts/txt_translation_runtime.py (MINIMAL MODIFY)

**Location**: `_translate_txt_with_runtime_pipeline()` function, after `orchestrator.execute()`

**Change**: Persist `context_state_metadata` to chunk record

```python
# Current (lines ~912-922):
result = {
    "status": "success",
    "output_path": str(chunk_file),
    "package_id": package["package_id"],
    "attempt": 1,
    "qa": qa_report,
    "runtime_pipeline": True,
    "orchestrator_version": orchestrator.version,
    "session_id": session_id,
}

# Proposed:
result = {
    "status": "success",
    "output_path": str(chunk_file),
    "package_id": package["package_id"],
    "attempt": 1,
    "qa": qa_report,
    "runtime_pipeline": True,
    "orchestrator_version": orchestrator.version,
    "session_id": session_id,
    "metadata": {  # ADD
        "context_state": context_state_metadata
    } if enable_cross_chunk_context else {},
}
```

**Also in legacy path** (`translate_txt()` function ~line 2383):
```python
records.append(result | {"chunk_index": idx, "chunk_total": len(chunks), "metadata": {"context_state": context_state_metadata} if enable_cross_chunk_context else {}})
```

**Impact**: Enables RM-8.2 → RM-8.3 provenance chain

---

### 2. ntpe_production_translate.py (MINIMAL MODIFY)

**Location**: `run_txt()` function (~line 354-388) and `run_batch()` function (~line 391-429)

**Change**: Pass `quality_delivery_formats_v83` to options

```python
# In run_txt():
options = TxtTranslationOptions(
    # ... existing fields ...
    quality_delivery_v83=args.quality_delivery_v83,
    quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if hasattr(args, 'quality_delivery_formats_v83') and args.quality_delivery_formats_v83 else ("txt",),
)

# In run_batch() — verify BatchTranslationOptions has this field, add if missing
```

**Impact**: Enables `--quality-delivery-formats-v83 epub pdf` from CLI

---

### 3. core/adapters/ (NEW DIRECTORY + 5 FILES)

| File | Purpose |
|------|---------|
| `canonical_book_intake_adapter.py` | Wrap `BookIntakeProcessor` |
| `epub_extraction_boundary.py` | EPUB → TXT extraction |
| `production_submission_adapter.py` | Submit to production CLI |
| `progress_checkpoint_adapter.py` | Parse resume/progress JSON |
| `rm8_delivery_adapter.py` | Trigger delivery pipeline |

---

### 4. web/reader/app/ (NEW DIRECTORY)

**Structure**:
```
web/reader/app/
├── package.json
├── tsconfig.json
├── next.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── jobs/
│   │   │   ├── page.tsx
│   │   │   └── [jobId]/
│   │   │       └── page.tsx
│   │   └── api/
│   │       └── translation/
│   │           └── route.ts
│   ├── components/
│   ├── lib/
│   └── hooks/
��── public/
```

---

## Files Explicitly Protected (DO NOT MODIFY)

| File/Directory | Protection Reason |
|----------------|-------------------|
| `core/book_intake/` | Frozen Stage 2.8 — governance freeze |
| `core/translation_runtime/runtime.py` | Stable facade — reuse only |
| `lts/txt_translation_runtime.py` | LTS baseline — only provenance fix allowed |
| `core/translation_release/delivery_pipeline.py` | RM-8.3 — works, wiring only |
| `core/translation_release/reader_structure/` | RM-8.4 — works, no changes |
| `core/translation_engine/` | Core engine — no changes |
| `core/ai_provider/` | Provider layer — no changes |
| `ui/translation_launcher/` | Quarantined — keep disabled |
| `web_ui/` | Legacy — reference only |
| `runtime_api/` | Legacy — reference only |
| `tools/` | Developer tools — no changes |
| `archive/` | Never imported by runtime — no changes |

---

## Change Budget Compliance

| Category | Allowed | P0 Plan |
|----------|---------|---------|
| New Reader UI | �� | `web/reader/app/` |
| Adapters | �� | 5 adapters in `core/adapters/` |
| Necessary wiring | �� | CLI format flag, provenance persistence |
| Necessary tests | �� | Adapter tests, integration tests |
| Necessary docs | �� | API docs, user guide |
| Provider修改 | ��� | None |
| Prompt修改 | ��� | None |
| Chunking修改 | ��� | None |
| Translation algorithm修改 | ��� | None |
| Retranslation | ��� | None |
| RM-8.5 semantic gate redesign | ��� | None |
| Archive migration | ��� | None |
| 大規模 legacy deletion | ��� | None |
| 新 runtime | ��� | Reuse existing |
| 新 launcher | ��� | Reuse existing |
| 新 checkpoint SoT | ��� | Reuse LTS JSON |

---

## Implementation Sequence

1. **Adapters first** (independent, testable):
   - `CanonicalBookIntakeAdapter` — wraps frozen intake
   - `ProgressCheckpointAdapter` — parses existing JSON
   - `ProductionSubmissionAdapter` — CLI submission
   - `Rm8DeliveryAdapter` — delivery pipeline trigger
   - `EpubExtractionBoundary` — EPUB extraction (can be deferred)

2. **Runtime fix** (minimal):
   - Persist `context_state_metadata` in `lts/txt_translation_runtime.py`

3. **CLI fix** (minimal):
   - Wire `quality_delivery_formats_v83` in `ntpe_production_translate.py`

4. **Reader Web App** (main work):
   - Next.js app in `web/reader/app/`
   - Integrates all adapters
   - Job submission, progress polling, delivery trigger

5. **Tests & Docs**:
   - Adapter unit tests
   - Integration tests (CLI → runtime → delivery)
   - User guide, API reference

---

## Risk / Contract Drift

| Risk | Mitigation |
|------|------------|
| Provenance fix breaks legacy path | Test both `runtime` and `legacy` pipeline modes |
| CLI format flag not in BatchTranslationOptions | Verify and add if missing |
| EPUB extraction dependency (`ebooklib`) | Optional, graceful degradation |
| Reader Web App → CLI subprocess reliability | Robust error handling, job tracking |
| Governance approval for `web/reader/` | Pre-validated in `P0_UI_DIRECTORY_PROPOSAL.md` |