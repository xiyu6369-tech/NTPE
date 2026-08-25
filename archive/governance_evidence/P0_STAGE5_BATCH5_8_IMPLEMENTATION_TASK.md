# P0 Stage 5 Batch 5.8 Implementation Task

## 1. Objective

Resolve the two verification gaps from Stage 5 Integrated Review:
1. Fix LTS import failure blocking runtime pipeline execution
2. Demonstrate Series Knowledge → PromptBuilder production reachability via deterministic offline E2E tests

**Deliverable**: Working end-to-end translation execution with Series context, proven through offline tests (Provider=0, Network=0, Translation=0).

---

## 2. Preconditions

- Baseline commit: `9f3d906` (Batch 5.7)
- Repository governance baseline established (RM-3.1)
- `NTPE_RUNTIME_PIPELINE=runtime` (default)
- Passion 6-book fixture available at `tests/fixtures/passion_6book/`
- All Stage 5.1–5.7 components verified operational

---

## 3. Authorized Production Files

| File | Change | Justification |
|------|--------|---------------|
| `lts/txt_translation_runtime.py` | Add 1 import line | Restore Batch 3D integration boundary |

**Exact Change** (after line 65, before line 66):
```python
from core.character_memory_v2 import (
    MemoryStore,
    load_or_create_character_memory,  # ADD THIS
)
```

---

## 4. Authorized Test Files

| File | Changes |
|------|---------|
| `tests/series/test_batch5_7_orchestration.py` | Unskip 2 tests, add 6 new test methods |

---

## 5. Forbidden Files

**DO NOT MODIFY**:
- Any file in `core/` except test file
- Any file in `lts/` except the single import
- Any governance document in `docs/governance/`
- Any file in `tools/`, `archive/`, root directory
- Any frozen contract file (see Section 15)

---

## 6. Exact LTS Fix

**File**: `lts/txt_translation_runtime.py`

**Location**: Lines 65-71 (import block)

**Before**:
```python
from core.character_memory_v2 import MemoryStore
from core.context_scene_memory import (
    ContextMemoryStore,
    load_context_memory,
    save_context_memory,
    load_or_create_context_memory,
)
```

**After**:
```python
from core.character_memory_v2 import (
    MemoryStore,
    load_or_create_character_memory,
)
from core.context_scene_memory import (
    ContextMemoryStore,
    load_context_memory,
    save_context_memory,
    load_or_create_context_memory,
)
```

**Verification**: `python -c "from lts.txt_translation_runtime import translate_txt"` succeeds.

---

## 7. Exact Series Context Integration Verification

**Test**: `test_translate_txt_without_series_context` (unskip)

**Setup**:
```python
runtime = TranslationRuntime(root=output_root)
options = TxtTranslationOptions(
    input_path=source_file,
    output_dir=output_dir,
    dry_run=True,
)
result = runtime.translate_txt(options)
assert result["status"] == "success"
```

**Verification**: Backward compatibility — translation works without series context.

---

**Test**: `test_translate_txt_with_series_context_none` (unskip)

**Setup**:
```python
runtime = TranslationRuntime(root=output_root)
runtime.set_series_context(None, None, None, None, None, None)
options = TxtTranslationOptions(...)
result = runtime.translate_txt(options, series_id="test", book_identity="test")
assert result["status"] == "success"
```

**Verification**: None context handled gracefully.

---

**Test**: `test_series_knowledge_reaches_mergedruntime` (NEW)

**Setup**:
1. Create series, add Book 1, translate Book 1 (dry-run), promote Book 1
2. Build SeriesContext for Book 2
3. Inject into Runtime
4. Execute `_translate_txt_with_runtime_pipeline` with dry-run
5. Capture `KnowledgeRuntimeManager._merged_runtime`

**Assertions**:
```python
merged = km.get_merged_runtime()
char_domain = merged.get_domain("character")
glossary_domain = merged.get_domain("glossary")
assert char_domain is not None
assert char_domain.entry_count > 0  # Series facts present
assert glossary_domain is not None
assert glossary_domain.entry_count > 0  # Series terms present
```

---

**Test**: `test_mergedruntime_reaches_promptbuilder` (NEW)

**Setup**: Same as above, but capture PromptAssembly

**Assertions**:
```python
assembly = builder.build(merged)
char_section = next(s for s in assembly.sections if s.name == "Character")
glossary_section = next(s for s in assembly.sections if s.name == "Glossary")
entity_section = next(s for s in assembly.sections if s.name == "Entity Mapping")
assert "鄭泰義" in char_section.content  # Series character fact
assert "家門" in glossary_section.content  # Series glossary term
assert entity_section.metadata["entity_count"] > 0
```

---

## 8. Exact 2-Book E2E Flow

**Test**: `test_two_book_series_e2e` (NEW)

**Series A — Book 1**:
```python
# Create series
create_result = coordinator.create_series("Passion", "Passion")
series_id = create_result.series_id

# Add Book 1
source_file = passion_fixture_dir / "passion_v01.txt"
book1_result = coordinator.add_book(series_id, source_file, "Passion 第1卷")

# Translate Book 1 (dry-run)
report1 = coordinator.translate_book(series_id, 1, dry_run=True)
assert report1.status == "success"

# Promote Book 1 (MANUAL gate)
promo_report = coordinator.promote_book(series_id, 1, approval_gate=True)
assert promo_report.series_memory_hash != ""
assert promo_report.series_glossary_hash != ""
assert promo_report.series_knowledge_hash != ""
```

**Series A — Book 2**:
```python
# Add Book 2
source_file2 = passion_fixture_dir / "passion_v02.txt"
book2_result = coordinator.add_book(series_id, source_file2, "Passion 第2卷")

# Translate Book 2 (dry-run) — should inherit Series context
report2 = coordinator.translate_book(series_id, 2, dry_run=True)
assert report2.status == "success"
```

**Verification**: Book 2 translation executes with Series context (hydration occurred).

---

## 9. Exact Promotion Flow

**Test**: `test_promotion_updates_all_series_hashes` (NEW)

**Verification**:
```python
# After promote_book:
assert series_registry.get(series_id).series_memory_hash == promo_report.series_memory_hash
assert series_registry.get(series_id).series_entity_registry_hash == promo_report.series_entity_registry_hash
assert series_registry.get(series_id).series_glossary_hash == promo_report.series_glossary_hash
assert series_registry.get(series_id).series_knowledge_hash == promo_report.series_knowledge_hash

# Book status updated
book_entry = series_registry.get(series_id).get_book(1)
assert book_entry.status.value == "promoted"
```

---

## 10. Exact Checkpoint Flow

**Test**: `test_checkpoint_resume_e2e` (NEW)

**Flow**:
```python
# 1. Translate Book 1 (few chunks, dry-run creates checkpoint)
report = coordinator.translate_book(series_id, 1, dry_run=True)

# 2. Verify checkpoint created
checkpoint = series_checkpoint_manager.load_latest_checkpoint(series_id)
assert checkpoint is not None
assert len(checkpoint.book_checkpoints) == 1
book_ref = checkpoint.book_checkpoints[0]
assert book_ref.status == "completed"  # dry_run completes chunks

# 3. Resume series
resume_report = coordinator.resume_series(series_id)
assert resume_report.series_checkpoint_id == checkpoint.checkpoint_id
assert len(resume_report.books_to_resume) >= 0  # May be 0 if all completed

# 4. Resume book (simulate interruption at chunk 5)
# Manually create checkpoint with status="in_progress"
# Then resume_book_in_series should restore chunk_index
```

**Invalid Checkpoint Rejection** (part of same test):
```python
# Wrong series_id
with pytest.raises(SeriesCheckpointIntegrityError):
    resume_book_in_series("wrong_series", book_identity, ...)

# Wrong book_identity
with pytest.raises(ValueError):
    resume_book_in_series(series_id, "wrong_book", ...)

# Invalid fingerprint (corrupt checkpoint file)
```

---

## 11. Cross-Series Isolation Tests

**Test**: `test_cross_series_isolation_promptbuilder` (NEW)

**Setup**:
```python
# Series A
series_a_result = coordinator.create_series("Series A", "Series A")
coordinator.add_book(series_a_result.series_id, book1_path, "Book 1")
coordinator.translate_book(series_a_result.series_id, 1, dry_run=True)
coordinator.promote_book(series_a_result.series_id, 1, approval_gate=True)

# Series B
series_b_result = coordinator.create_series("Series B", "Series B")
coordinator.add_book(series_b_result.series_id, book1_path, "Book 1")
coordinator.translate_book(series_b_result.series_id, 1, dry_run=True)
coordinator.promote_book(series_b_result.series_id, 1, approval_gate=True)

# Build context for each and verify isolation
context_a = build_series_context(series_a, book_identity_a, ...)
context_b = build_series_context(series_b, book_identity_b, ...)

# Inject into separate runtimes
inject_series_context(runtime_a, context_a, ...)
inject_series_context(runtime_b, context_b, ...)

# Execute and capture PromptAssembly
assembly_a = builder_a.build(merged_a)
assembly_b = builder_b.build(merged_b)

# Verify different content
char_a = next(s for s in assembly_a.sections if s.name == "Character").content
char_b = next(s for s in assembly_b.sections if s.name == "Character").content
assert char_a != char_b  # Different series = different content
```

---

## 12. Dry-Run Requirements

**Test**: `test_dry_run_safety_offline` (NEW)

**Requirements**:
- `options.dry_run = True`
- Provider Execution = 0
- Network Execution = 0
- Translation Execution = 0

**Verification**:
```python
# Runtime execution with dry_run
result = _translate_txt_with_runtime_pipeline(
    options=TxtTranslationOptions(..., dry_run=True),
    ...
)

# All chunks should be dry_run status
for record in result["records"]:
    assert record["status"] == "dry_run"
    assert record["attempt"] == 0

# No provider calls made (verify via mock or log inspection)
# No network calls (verify via mock or log inspection)
# No translation output written (chunks empty)
```

**Series State Mutation Check**:
```python
# Series artifacts must NOT be mutated by dry-run
memory_hash_before = series_memory_store.series_memory_hash
glossary_hash_before = series_glossary.glossary_hash
knowledge_hash_before = series_knowledge.knowledge_hash

result = coordinator.translate_book(series_id, 1, dry_run=True)

memory_hash_after = series_memory_store.series_memory_hash
assert memory_hash_after == memory_hash_before
# Same for glossary, knowledge
```

---

## 13. Offline Requirements

- **NO** network requests
- **NO** real provider calls
- **NO** external API calls
- **NO** real translation execution
- All tests use `dry_run=True` or fake provider boundary
- All fixtures are repository-local (`tests/fixtures/passion_6book/`)

---

## 14. Provider/Network Restrictions

**Enforced by Test Design**:
```python
# All test entry points use dry_run=True
options = TxtTranslationOptions(..., dry_run=True)

# Or validate_dry_run_safety()
validate_dry_run_safety(
    "translate",
    mutates_state=False,  # Series state
    calls_provider=False,
    performs_network=False,
    executes_translation=False,
)
```

**CI Verification**: Test runner must not have provider credentials configured.

---

## 15. Frozen Contract Requirements

**Batch 5.8 MUST NOT Modify**:

| Contract | File(s) |
|----------|---------|
| Foundation frozen contracts | `docs/governance/repository/FOUNDATION_FROZEN_CONTRACTS.md` |
| Character Memory v2 core | `core/character_memory_v2/models.py`, `store.py`, `validation.py` |
| Context/Scene Memory core | `core/context_scene_memory/models.py`, `store.py` |
| Entity Resolver | `core/entity_resolver/resolver.py`, `extractor.py` |
| KnowledgeRuntime frozen layers | `core/knowledge_runtime/merger.py`, `models.py`, `resolver.py` |
| Runtime Checkpoint | `core/runtime_checkpoint/models.py`, `manager.py` |
| Production Runtime Checkpoint | `core/runtime_checkpoint/manager.py` |
| Translation Session Checkpoint | `core/runtime_session/models.py`, `manager.py` |
| Translation Pipeline | `core/translation_pipeline/*` |

**Allowed**: Single import addition to `lts/txt_translation_runtime.py` (additive compatibility fix).

---

## 16. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | LTS import fixed | `python -c "from lts.txt_translation_runtime import translate_txt"` |
| 2 | translate without series context | `test_translate_txt_without_series_context` PASS |
| 3 | translate with None series context | `test_translate_txt_with_series_context_none` PASS |
| 4 | Series Knowledge → MergedRuntime | `test_series_knowledge_reaches_mergedruntime` PASS |
| 5 | MergedRuntime → PromptBuilder | `test_mergedruntime_reaches_promptbuilder` PASS |
| 6 | PromptBuilder receives Series glossary | Same test — GlossarySection content |
| 7 | PromptBuilder receives Series entity mapping | Same test — EntityMappingSection |
| 8 | PromptBuilder receives Series memory | Same test — CharacterSection content |
| 9 | Book 1 promotion updates hashes | `test_promotion_updates_all_series_hashes` PASS |
| 10 | Book 2 inherits Series context | `test_two_book_series_e2e` PASS |
| 11 | Series A ≠ Series B context | `test_cross_series_isolation_promptbuilder` PASS |
| 12 | Checkpoint created with valid hashes | `test_checkpoint_resume_e2e` PASS |
| 13 | Resume from checkpoint works | Same test — resume_book_in_series |
| 14 | Invalid checkpoint rejected | Same test — wrong series/book/fingerprint |
| 15 | Dry-run: Provider=0 | `test_dry_run_safety_offline` PASS |
| 16 | Dry-run: Network=0 | Same test |
| 17 | Dry-run: Translation=0 | Same test |
| 18 | Dry-run: Series state not mutated | Same test — hash comparison |
| 19 | All existing tests still PASS | `pytest tests/series/test_batch5_7_orchestration.py -v` |
| 20 | `ntpe_validate.py` ALL PASS | `python ntpe_validate.py` |
| 21 | `compileall` 0 errors | `python -m compileall .` |
| 22 | `git diff --check` clean | `git diff --check` |

---

## 17. Test Commands

```bash
# Run Batch 5.8 tests
python -m pytest tests/series/test_batch5_7_orchestration.py -v

# Run specific new tests
python -m pytest tests/series/test_batch5_7_orchestration.py::TestTranslationRuntimeSeriesContext -v

# Full validation
python ntpe_validate.py

# Compile check
python -m compileall .

# Git diff check
git diff --check
```

---

## 18. Failure Classification

| Failure | Classification | Action |
|---------|----------------|--------|
| LTS import fails | BLOCKER | Fix import, re-verify |
| Dry-run calls provider | BLOCKER | Fix dry-run path |
| Series context not in PromptBuilder | BLOCKER | Debug injection path |
| Promotion doesn't update hashes | BLOCKER | Debug promotion flow |
| Checkpoint validation fails | BLOCKER | Debug hash computation |
| Cross-series isolation fails | BLOCKER | Debug registry/validation |
| Existing test regresses | BLOCKER | Restore behavior |
| `ntpe_validate.py` fails | BLOCKER | Fix governance violation |
| `compileall` errors | BLOCKER | Fix syntax/import |

---

## 19. Stop Conditions

**STOP IMMEDIATELY if**:
- Any production file modified beyond authorized import
- Any frozen contract modified
- Any test requires network/provider/translation
- `ntpe_validate.py` reports violations
- Git diff shows changes to forbidden files

---

## 20. Git Delivery Boundary

**Single Commit** containing:
1. `lts/txt_translation_runtime.py` — 1 line import addition
2. `tests/series/test_batch5_7_orchestration.py` — Unskip 2 tests + 6 new test methods

**Commit Message Format**:
```
P0 Stage 5 Batch 5.8 — LTS Integration & E2E Verification

- Fix LTS import: add load_or_create_character_memory to lts/txt_translation_runtime.py
- Unskip 2 translation runtime tests
- Add 2-book Series E2E test (Book 1→promotion→Book 2 inheritance)
- Add Series A/B cross-isolation PromptBuilder test
- Add checkpoint/resume E2E test with invalid rejection
- Add dry-run safety test (Provider=0, Network=0, Translation=0)
- Add PromptBuilder context verification test

All tests offline (dry-run), Provider=0, Network=0, Translation=0.
Frozen contracts respected. Governance validated.
```

**Branch**: `p0-stage5-batch5.8-lts-integration-e2e`

**Base**: `9f3d906` (Batch 5.7 baseline)