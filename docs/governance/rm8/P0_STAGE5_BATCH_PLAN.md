# P0 Stage 5 ??Batch Plan

**Baseline Commit:** `4b7b8781bae035466dc215ca0a265052f0055cda`
**Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md`
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_SERIES_CONTINUITY_PREFLIGHT_AUDIT.md`
**Status:** Batch Plan ??Awaiting Owner Authorization for Batch 5.1

---

## Batch Overview

| Batch | Name | New Modules | Modified Modules | Duration |
|-------|------|-------------|------------------|----------|
| **5.1** | Series Identity & Manifest | `core/series_identity/` | ??| 1 week |
| **5.2** | Series Memory Store | `core/series_memory/` | `core/character_memory_v2/` (hydration only) | 2 weeks |
| **5.3** | Series Entity Registry | `core/series_entity_registry/` | `core/entity_resolver/` (integration only) | 1 week |
| **5.4** | Series Glossary | ??| `core/glossary_builder.py` | 1 week |
| **5.5** | Series Knowledge Population | ??| `core/knowledge_runtime/` (Novel tier) | 1 week |
| **5.6** | Series Checkpoint Hierarchy | `core/series_checkpoint/` | ??| 1 week |
| **5.7** | Series Orchestration | `core/series_orchestration/` | `core/translation_runtime/` (optional series context) | 2 weeks |
| **5.8** | Migration & Compatibility | ??| All persistence modules (optional series_id) | 1 week |
| **5.9** | Validation & Freeze | ??| `ntpe_validate.py`, Foundation Manifest | 1 week |

---

## Batch 5.1 ??Series Identity & Manifest

### Scope
Establish Series identity foundation: deterministic `series_id`, `SeriesManifest`, `SeriesRegistry`, persistence.

### New Files
```
core/series_identity/
?œâ??€ __init__.py
?œâ??€ models.py              # SeriesManifest, BookRef, SeriesIdentity
?œâ??€ registry.py            # SeriesRegistry (create, get, list, add_book)
?œâ??€ persistence.py         # Load/save series_manifest_{series_id}.json
?œâ??€ validation.py          # Manifest schema validation, hash verification
?”â??€ identity.py            # compute_series_id, compute_book_identity (re-export)
```

### Allowed Modifications
- **NEW** `core/series_identity/` module (complete)
- **NEW** `docs/governance/rm8/series_identity_contract.md` (contract doc)

### Forbidden Modifications
- Any existing `core/character_memory_v2/`, `core/context_scene_memory/`, `core/entity_resolver/`, `core/knowledge_runtime/`, `core/book_intake/`, `core/translation_runtime/`, `core/translation_pipeline/`, `core/production_runtime/`, `core/runtime_checkpoint/`
- Any Frozen Contract (9 existing)
- Any production code behavioral change

### Tests
| Test | Description |
|------|-------------|
| `test_series_id_deterministic` | Same name ??same ID across runs/machines |
| `test_manifest_roundtrip` | Save ??load ??hash matches |
| `test_book_ordering` | volume_number sequential, immutable |
| `test_manifest_validation` | Invalid schema/hash ??exception |
| `test_cross_series_isolation` | Series A manifest independent of Series B |
| `test_add_book_idempotent` | Add same book twice ??no duplicate |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] `ntpe_validate.py` PASS (no new warnings)
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] Manifest persistence deterministic (100 runs same hash)

### Rollback Boundary
- Delete `core/series_identity/` directory
- No other files modified ??clean rollback

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation

---

## Batch 5.2 ??Series Memory Store

### Scope
Canonical Series-level character facts (`SeriesCharacterRecord`), `SeriesMemoryStore`, hydration (Series?’Book), promotion (Book?’Series).

### New Files
```
core/series_memory/
?œâ??€ __init__.py
?œâ??€ models.py              # SeriesCharacterRecord, SeriesFactRecord
?œâ??€ store.py               # SeriesMemoryStore (CRUD, query)
?œâ??€ persistence.py         # Load/save series_memory_{series_id}.json
?œâ??€ hydration.py           # SeriesMemoryStore ??BookMemoryStore
?œâ??€ promotion.py           # BookMemoryStore ??SeriesMemoryStore (with approval gate)
?œâ??€ validation.py          # Series memory validation, conflict detection
?”â??€ mapping.py             # korean_to_series_id, series_id_to_book_ids
```

### Modified Files (Additive Only)
- `core/character_memory_v2/persistence.py` ??Add optional `series_id` parameter to `load_or_create_character_memory()`, call `hydrate_from_series()` if provided
- `core/character_memory_v2/__init__.py` ??Re-export hydration function

### Allowed Modifications
- **NEW** `core/series_memory/` module (complete)
- **ADDITIVE** `core/character_memory_v2/persistence.py` ??Optional series hydration parameter
- **ADDITIVE** `core/character_memory_v2/__init__.py` ??Export new function

### Forbidden Modifications
- `core/character_memory_v2/models.py` ??**FROZEN**
- `core/character_memory_v2/store.py` ??**FROZEN** (`MemoryStore`, `add_or_merge_memory`, conflict resolution, evidence ranking)
- `core/character_memory_v2/lifecycle.py` ??**FROZEN**
- `core/character_memory_v2/selection.py` ??**FROZEN**
- `core/character_memory_v2/validation.py` ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_series_character_record_crud` | Create, read, update canonical records |
| `test_hydration_roundtrip` | Series ??Book ??Series (promotion) ??same canonical facts |
| `test_hydration_idempotent` | Hydrate twice ??same BookMemoryStore state |
| `test_promotion_conflict_detection` | Different values ??conflict exception |
| `test_promotion_approval_gate` | Policy=manual ??requires approval |
| `test_namespace_isolation` | Series A "?Žæ?" ??Series B "?Žæ?" |
| `test_canonical_fact_immutability` | Only APPROVED facts in SeriesMemoryStore |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] Integration test: Book 1 translate ??promote ??Book 2 hydrate ??canonical names present
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] No regression in existing Character Memory v2 tests

### Rollback Boundary
- Delete `core/series_memory/` directory
- Revert `core/character_memory_v2/persistence.py` to baseline
- Revert `core/character_memory_v2/__init__.py` to baseline

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation

---

## Batch 5.3 ??Series Entity Registry

### Scope
Persistent Series-level entity registry (`SeriesEntityRecord`, `SeriesEntityRegistry`), EntityResolver integration with SERIES precedence.

### New Files
```
core/series_entity_registry/
?œâ??€ __init__.py
?œâ??€ models.py              # SeriesEntityRecord
?œâ??€ registry.py            # SeriesEntityRegistry (CRUD, query)
?œâ??€ persistence.py         # Load/save series_entities_{series_id}.json
?œâ??€ integration.py         # EntityResolver integration helper
?”â??€ validation.py          # Registry validation
```

### Modified Files (Additive Only)
- `core/entity_resolver/resolver.py` ??Add optional `series_registry` parameter to `__init__`, check series registry in `_resolve_single` (before RUNTIME)
- `core/entity_resolver/__init__.py` ??Re-export SeriesEntityRegistry
- `core/entity_resolver/extractor.py` ??`build_known_entities_from_runtime()` accepts optional `series_registry`

### Allowed Modifications
- **NEW** `core/series_entity_registry/` module (complete)
- **ADDITIVE** `core/entity_resolver/resolver.py` ??Optional series_registry parameter, precedence insertion
- **ADDITIVE** `core/entity_resolver/extractor.py` ??Optional series_registry parameter
- **ADDITIVE** `core/entity_resolver/__init__.py` ??Export new class

### Forbidden Modifications
- `core/entity_resolver/models.py` ??**FROZEN** (ResolvedEntity, EntityInjectionSet, InjectionSource enum)
- `core/entity_resolver/injector.py` ??**FROZEN**
- `core/entity_resolver/_resolve_single` core logic ??Only additive series registry check
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_series_entity_registry_crud` | Create, read, update, delete series entities |
| `test_resolver_precedence` | SERIES > RUNTIME > LEARNING > AUTO |
| `test_series_override_persists` | Close/open NTPE ??series overrides retained |
| `test_cross_series_isolation` | Series A entity not visible in Series B resolver |
| `test_integration_with_extractor` | Series entities appear in known_entities for extraction |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] Integration test: Series entity resolved in Book 2 without user override
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] No regression in existing Entity Resolver tests

### Rollback Boundary
- Delete `core/series_entity_registry/` directory
- Revert `core/entity_resolver/resolver.py` to baseline
- Revert `core/entity_resolver/extractor.py` to baseline
- Revert `core/entity_resolver/__init__.py` to baseline

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Batch 5.4 ??Series Glossary

### Scope
Series-canonical glossary (`SeriesGlossary`), integration with `GlossaryBuilder` for cross-volume canonical terms.

### New Files
- None (extends existing `core/glossary_builder.py`)

### Modified Files (Additive Only)
- `core/glossary_builder.py` ??Add `build_series_glossary()`, `load_series_glossary()`, `merge_into_series_glossary()` functions
- `core/glossary_builder.py` ??Series glossary persistence: `series_glossary_{series_id}.json`

### Allowed Modifications
- **ADDITIVE** `core/glossary_builder.py` ??New functions, series glossary I/O
- **NEW** `docs/governance/rm8/series_glossary_contract.md`

### Forbidden Modifications
- `core/glossary.py` ??**FROZEN** (Glossary class, prompt_block, apply_output_fix)
- `core/translation_resources/glossary_resource.py` ??**FROZEN**
- `core/literary/glossary_context.py` ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_series_glossary_build` | Build from completed books only |
| `test_series_glossary_merge` | Merge Book 1 + Book 2 ??canonical terms |
| `test_series_glossary_hydration` | Series glossary ??Book glossary locked terms |
| `test_locked_term_precedence` | Series locked term overrides book auto term |
| `test_cross_series_isolation` | Series A glossary independent of Series B |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] Integration test: Book 2 translation uses Series glossary terms
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] No regression in existing Glossary Builder tests

### Rollback Boundary
- Revert `core/glossary_builder.py` to baseline
- Delete any `series_glossary_*.json` test artifacts

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Batch 5.5 ??Series Knowledge Population

### Scope
Populate KnowledgeRuntime Novel/Volume tiers from SeriesMemoryStore and SeriesGlossary.

### Modified Files (Additive Only)
- `core/knowledge_runtime/manager.py` ??Add `load_series_knowledge(series_id)` to populate Novel tier
- `core/knowledge_runtime/merger.py` ??Ensure Novel tier populated before merge
- `core/knowledge_runtime/loader.py` ??Add series knowledge source loading

### Allowed Modifications
- **ADDITIVE** `core/knowledge_runtime/manager.py` ??Series knowledge loading
- **ADDITIVE** `core/knowledge_runtime/loader.py` ??Series domain source

### Forbidden Modifications
- `core/knowledge_runtime/models.py` ??**FROZEN**
- `core/knowledge_runtime/merger.py` core logic (`KnowledgeMerger`, `DOMAIN_STRATEGIES`, `SnapshotHierarchy`) ??**FROZEN**
- `core/knowledge_runtime/snapshot.py` ??**FROZEN**
- `core/knowledge_runtime/resolver.py` ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_novel_tier_populated` | Series canonical facts ??Novel tier in KnowledgeMerger |
| `test_volume_tier_per_book` | Book-specific facts ??Volume tier |
| `test_resolver_queries_novel` | EntityResolver queries Series knowledge via MergedRuntime |
| `test_hierarchy_precedence` | Chunk > Chapter > Volume > Novel (KEY_OVERRIDE/REPLACE) |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] Integration test: Series canonical name resolved via KnowledgeRuntime
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] No regression in existing Knowledge Runtime tests

### Rollback Boundary
- Revert `core/knowledge_runtime/manager.py` to baseline
- Revert `core/knowledge_runtime/loader.py` to baseline

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Batch 5.6 ??Series Checkpoint Hierarchy

### Scope
4-level checkpoint hierarchy (Series/Book/Session/Chunk), `SeriesCheckpointManager`, recovery orchestration.

### New Files
```
core/series_checkpoint/
?œâ??€ __init__.py
?œâ??€ models.py              # SeriesCheckpoint, BookCheckpointRef, SessionCheckpointRef
?œâ??€ manager.py             # SeriesCheckpointManager
?œâ??€ persistence.py         # Load/save series_checkpoint_{series_id}.json
?œâ??€ recovery.py            # Recovery orchestration (series ??book ??session)
?”â??€ validation.py          # Checkpoint hash validation, integrity
```

### Allowed Modifications
- **NEW** `core/series_checkpoint/` module (complete)

### Forbidden Modifications
- `core/runtime_checkpoint/` ??**FROZEN** (models, manager, validator)
- `core/production_runtime/checkpoint.py` ??**FROZEN**
- `core/translation_session/session_checkpoint.py` ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_series_checkpoint_creation` | Series checkpoint with all hashes |
| `test_4level_hierarchy` | Series ??Book ??Session ??Chunk refs |
| `test_recovery_series` | Load series checkpoint ??restore all levels |
| `test_recovery_book_in_series` | Resume Book 2 from series checkpoint |
| `test_hash_integrity` | Corrupted checkpoint ??exception |
| `test_checkpoint_idempotent` | Save twice ??same hash |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] Integration test: Full series resume after NTPE restart
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] No regression in existing Checkpoint tests

### Rollback Boundary
- Delete `core/series_checkpoint/` directory

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Batch 5.7 ??Series Orchestration

### Scope
`SeriesTranslationCoordinator`, multi-book workflow, UX integration (CLI/launcher), series-aware translation runtime.

### New Files
```
core/series_orchestration/
?œâ??€ __init__.py
?œâ??€ coordinator.py         # SeriesTranslationCoordinator
?œâ??€ workflow.py            # Multi-book workflow state machine
?œâ??€ cli_integration.py     # CLI commands: series create, add-book, promote-book
?œâ??€ runtime_integration.py # TranslationRuntime series context injection
?”â??€ validation.py          # Workflow validation
```

### Modified Files (Additive Only)
- `core/translation_runtime/runtime.py` ??Add optional `series_id`, `book_identity` to `translate_txt()`, `translate_package()`
- `core/translation_runtime/__init__.py` ??Export series-aware functions
- `ntpe_launcher.py` ??Add series commands (optional, behind flag)

### Allowed Modifications
- **NEW** `core/series_orchestration/` module (complete)
- **ADDITIVE** `core/translation_runtime/runtime.py` ??Optional series context parameters
- **ADDITIVE** `ntpe_launcher.py` ??Series CLI commands (additive)

### Forbidden Modifications
- `core/translation_runtime/runtime.py` core TXT/batch logic ??**FROZEN**
- `core/translation_pipeline/` ??**FROZEN**
- `core/book_intake/` ??**FROZEN**
- `core/production_runtime/` ??**FROZEN**
- `lts/` ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_series_create` | `ntpe series create "Passion"` ??SeriesManifest |
| `test_add_book` | `ntpe series add-book "Passion" file.txt` ??BookRef |
| `test_translate_with_series` | `ntpe translate --series "Passion" --book 1` ??hydrated |
| `test_promote_book` | `ntpe series promote-book "Passion" --book 1` ??SeriesMemoryStore updated |
| `test_full_passion_6book` | Book 1?? continuous with continuity |
| `test_backward_compat_txt` | TXT translation without series_id works identically |
| `test_backward_compat_epub` | EPUB workflow without series_id works identically |

### Acceptance Gates
- [ ] All unit tests PASS
- [ ] **Passion 6-book scenario PASS** (Book 1?? continuous translation with character/glossary continuity)
- [ ] Cross-series contamination test: 0 leaks
- [ ] Single-book TXT/EPUB regression: 0 failures
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean

### Rollback Boundary
- Delete `core/series_orchestration/` directory
- Revert `core/translation_runtime/runtime.py` to baseline
- Revert `ntpe_launcher.py` to baseline

### Provider/Network/Translation Policy
- **ZERO** provider calls (uses existing mock/dry-run paths)
- **ZERO** network requests
- **ZERO** real translation executions (test uses mock provider or dry-run)

---

## Batch 5.8 ??Migration & Compatibility

### Scope
LTS ??v2 ??Series migration, backward compatibility validation, regression test suite.

### Modified Files (Additive Only)
- `core/character_memory_v2/persistence.py` ??`migrate_lts_to_v2()` accepts optional `series_id` for direct series promotion
- `core/character_memory_v2/persistence.py` ??`load_or_create_character_memory()` full series integration
- `core/context_scene_memory/persistence.py` ??Series-aware initialization
- `core/translation_session/session.py` ??Series context in session metadata

### Allowed Modifications
- **ADDITIVE** persistence modules ??Optional series_id parameters, hydration calls
- **ADDITIVE** session module ??Series metadata

### Forbidden Modifications
- Any core model/store/lifecycle ??**FROZEN**
- Any Frozen Contract

### Tests
| Test | Description |
|------|-------------|
| `test_lts_to_v2_to_series` | LTS memory ??v2 ??SeriesMemoryStore promotion |
| `test_existing_book_memory_compat` | Pre-Stage 5 book memory loads, hydrates if series_id provided |
| `test_existing_checkpoint_compat` | Pre-Stage 5 checkpoints load, work without series |
| `test_no_series_id_regression` | All workflows work identically without series_id |
| `test_full_regression_suite` | All existing pytest tests PASS |

### Acceptance Gates
- [ ] All migration tests PASS
- [ ] Full existing test suite (888 tests) PASS
- [ ] `ntpe_validate.py` PASS
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean

### Rollback Boundary
- Revert all modified persistence/session files to baseline

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Batch 5.9 ??Validation & Freeze

### Scope
Update `ntpe_validate.py` for new contracts, freeze new contracts in Foundation Manifest, final documentation.

### Modified Files
- `ntpe_validate.py` ??Add Series contract validation
- `core/foundation/foundation_manifest_v1.json` ??Add 5 new frozen contracts
- `core/foundation/manifest.py` ??Update `REQUIRED_CONTRACTS`
- `docs/governance/rm8/` ??Final specification, batch reports, acceptance reports

### Allowed Modifications
- `ntpe_validate.py` ??Validation extensions
- `core/foundation/foundation_manifest_v1.json` ??Contract registry update
- `core/foundation/manifest.py` ??Contract list update
- Documentation files in `docs/governance/rm8/`

### Forbidden Modifications
- Any production code behavioral change
- Any Frozen Contract (existing 9)

### Tests
| Test | Description |
|------|-------------|
| `test_validate_series_contracts` | New contracts validated |
| `test_foundation_manifest_updated` | 14 total contracts (9 old + 5 new) |
| `test_ntpe_validate_all_pass` | Zero warnings |
| `test_final_acceptance` | Passion 6-book, cross-series, backward compat all PASS |

### Acceptance Gates
- [ ] `ntpe_validate.py` **ALL PASS (0 warnings)**
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] Foundation Manifest valid with 14 contracts
- [ ] All Stage 5 acceptance criteria met
- [ ] Documentation complete

### Rollback Boundary
- Revert `ntpe_validate.py`, `core/foundation/` to baseline
- Documentation rollback = delete new files

### Provider/Network/Translation Policy
- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions

---

## Cross-Batch Dependencies

```
5.1 (Identity) ?€?€?¬â??€??5.2 (Memory) ?€?€?¬â??€??5.7 (Orchestration)
                 ??                   ??                 ?œâ??€??5.3 (Entity) ?€?€?€??                 ??                   ??                 ?œâ??€??5.4 (Glossary) ?€??                 ??                   ??                 ?œâ??€??5.5 (Knowledge) ??                 ??                   ??                 ?”â??€??5.6 (Checkpoint)??                                    ??5.8 (Migration) ?â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??                                    ??5.9 (Validation) ?â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??```

**Critical Path:** 5.1 ??5.2 ??5.7 ??5.8 ??5.9
(5.3, 5.4, 5.5, 5.6 can parallelize after 5.1)

---

## Global Constraints (All Batches)

| Constraint | Enforcement |
|------------|-------------|
| No production code modification | Code review: only new `series_*` modules + additive optional params |
| No Frozen Contract modification | `ntpe_validate.py` enforces |
| No Provider/Network/Translation | CI: zero external calls in test runs |
| No feature flag activation | All series code behind explicit `series_id` parameter (opt-in) |
| Deterministic identity | Property tests: 1000 iterations same input ??same output |
| Artifact isolation | File structure validation in tests |
| Fail-closed | All loads validate hashes; corruption ??exception |

---

## Owner Authorization Checkpoints

| Checkpoint | Required Before |
|------------|-----------------|
| **Batch 5.1 Start** | Series ID source, Manifest storage format, Book ordering policy |
| **Batch 5.2 Start** | Promotion policy default (manual vs auto), Hydration scope |
| **Batch 5.3 Start** | Entity Registry precedence (confirmed SERIES > RUNTIME) |
| **Batch 5.7 Start** | CLI command design, Concurrent books policy (confirmed disallowed) |
| **Stage 5 Complete** | All acceptance gates PASS, Foundation Manifest updated |

---

## Recommended Next Authorization

**Immediate:** Authorize **Batch 5.1 (Series Identity & Manifest)** with confirmed decisions:
1. Series ID = user-provided name hash
2. Manifest = single JSON file per series
3. Book ordering = sequential volume_number (immutable)
4. Promotion default = manual for all fact types
5. Concurrent books = disallowed in Stage 5

**Upon authorization ??Begin Batch 5.1 implementation.**

---

*End of Batch Plan. No production code modified. Awaiting Owner authorization for Batch 5.1.*
