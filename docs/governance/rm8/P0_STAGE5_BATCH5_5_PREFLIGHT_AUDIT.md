# P0 Stage 5 Batch 5.5 — Series Knowledge Population Preflight Audit

**Baseline Commit:** `b13a6ec0df4882a060ba9cf02ed81e2803790a52` (P0 Stage 5 Batch 5.4 Accepted)
**Audit Date:** 2026-08-20
**Status:** Preflight Audit — No Production Code Modified

---

## 1. Executive Summary

This audit examines NTPE's current Knowledge Runtime architecture to establish the preflight analysis for **P0 Stage 5 Batch 5.5 — Series Knowledge Population**. The baseline includes:

- **Batch 5.1** (Series Identity & Manifest): `core/series_identity/` — `SeriesIdentity`, `SeriesManifest`, `SeriesRegistry`, deterministic `series_id`, `series_memory_hash`, `series_checkpoint_hash`, `series_entity_registry_hash`, `series_glossary_hash`
- **Batch 5.2** (Series Memory Store): `core/series_memory/` — `SeriesMemoryStore`, `SeriesCharacterRecord`, `SeriesFactRecord`, `SeriesNamespaceMapping`, hydration (Series→Book), promotion (Book→Series MANUAL gate)
- **Batch 5.3** (Series Entity Registry): `core/series_entity_registry/` — `SeriesEntityRecord`, `SeriesEntityRegistry`, EntityResolver integration via `user_overrides`
- **Batch 5.4** (Series Glossary): `core/glossary_builder.py` extensions — `SeriesGlossary`, `SeriesGlossaryTerm`, `build_series_glossary()`, `load_series_glossary()`, `merge_into_series_glossary()`, persistence `series_glossary_{series_id}.json`

**Primary Finding:** NTPE has a **complete Knowledge Runtime** (`core/knowledge_runtime/`) with hierarchical merge capability (Novel → Volume → Chapter → Chunk via `SnapshotHierarchy`). However, the **Novel and Volume tiers are unpopulated** — there is no Series-level knowledge source loading. The `KnowledgeLoader` only loads from in-memory `source` dict; no persistence, no Series domain, no cross-volume canonical knowledge.

**Batch 5.5 must establish:**
- Series knowledge source loading in `KnowledgeLoader` (SeriesMemoryStore → character/glossary domains, SeriesGlossary → glossary domain)
- `KnowledgeRuntimeManager.load_series_knowledge(series_id)` to populate Novel tier from Series sources
- Deterministic persistence: `series_knowledge_{series_id}.json` with SHA-256 integrity
- SeriesManifest integration via `series_knowledge_hash` derived field
- Volume tier population per book (BookMemoryStore → Volume tier)
- Cross-series isolation via `series_id` namespace
- CSI-04 hard gate for knowledge isolation

---

## 2. Existing Capability Inventory

### 2.1 Knowledge Runtime — Current State

| Component | Status | Details |
|-----------|--------|---------|
| **KnowledgeDomain enum** | Complete | CHARACTER, GLOSSARY, NARRATIVE, SCENE, STYLE, GENERAL |
| **KnowledgePrototype** | Complete | Immutable prototype for load/resolve handoffs |
| **KnowledgeEntry** | Complete | Resolved entry ready for runtime consumption |
| **KnowledgeBundle** | Complete | Collection of entries grouped by domain |
| **KnowledgeSnapshot** | Complete | Point-in-time snapshot of runtime state |
| **SnapshotHierarchy** | Complete | Novel → Volume → Chapter → Chunk layered hierarchy |
| **KnowledgeMerger** | Complete | Merges layered snapshots with KEY_OVERRIDE/REPLACE strategies |
| **MergedKnowledge** | Complete | Merged view for single domain |
| **MergedRuntime** | Complete | Complete merged runtime across all domains |
| **KnowledgeResolver** | Complete | Resolves exclusively from MergedRuntime |
| **KnowledgeSnapshotStore** | Complete | Store/retrieve/diff/merge snapshots |
| **KnowledgeLoader** | Complete | Loads from in-memory `source` dict only — **NO Series persistence** |
| **KnowledgeRuntimeManager** | Complete | Orchestrates Loader → Snapshot → Merger → Resolver |

**Critical Gap:** The hierarchy *has* Novel/Volume levels (`SnapshotHierarchy.ORDER = ["novel", "volume", "chapter", "chunk"]`) but **no mechanism populates them from Series-level sources**. All current loading is from ad-hoc in-memory dicts.

### 2.2 Series Memory Store (Batch 5.2) — `core/series_memory/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesCharacterRecord** | Complete | Canonical NEVER-expiry facts, `series_character_id = schar_{sha256(series_id\|korean)[:16]}` |
| **SeriesFactRecord** | Complete | Non-character canonical facts, `series_fact_id = sfact_{sha256(series_id\|type\|value)[:16]}` |
| **SeriesMemoryStore** | Complete | CRUD, `get_all_canonical_facts()`, `get_all_canonical_facts_by_type()`, hydration, promotion |
| **Persistence** | Complete | `output/series/{series_id}/series_memory_{series_id}.json` with fingerprint |
| **Fact Types** | Complete | CANONICAL_NAME, RELATIONSHIP, TERMINOLOGY_PREFERENCE, PHYSICAL_TRAIT, PERSONALITY, BACKGROUND, OTHER |

**Available for Knowledge Population:** All APPROVED canonical facts via `get_all_canonical_facts()` and `get_all_canonical_facts_by_type(FactType)`.

### 2.3 Series Glossary (Batch 5.4) — `core/glossary_builder.py`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesGlossary** | Complete | Persistent canonical glossary, `series_glossary_{series_id}.json` |
| **SeriesGlossaryTerm** | Complete | Locked terms with `locked=True` or `confidence>=0.95`, source_books provenance |
| **get_locked_dictionary()** | Complete | Returns `{source: translation}` for locked/high-confidence terms |
| **get_alias_map()** | Complete | Returns alias → translation mapping |
| **Persistence** | Complete | `output/series/{series_id}/series_glossary_{series_id}.json` |

**Available for Knowledge Population:** All locked/high-confidence glossary terms via `get_locked_dictionary()` and `get_alias_map()`.

### 2.4 Series Identity (Batch 5.1) — `core/series_identity/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesManifest** | Complete | Books with volume_number, status, `series_knowledge_hash` field **NOT YET ADDED** |
| **SeriesRegistry** | Complete | `update_series_knowledge_hash()` method **NOT YET ADDED** |
| **Derived Fields** | Complete | `series_memory_hash`, `series_checkpoint_hash`, `series_entity_registry_hash`, `series_glossary_hash` |

---

## 3. Current Knowledge Architecture — Gap Analysis

| Capability | Current State | Required for Batch 5.5 |
|------------|---------------|------------------------|
| **Series Knowledge Domain** | **NONE** — No `KnowledgeDomain.SERIES` enum | Add domain or use existing CHARACTER/GLOSSARY for Novel tier |
| **Novel Tier Population** | **UNPOPULATED** — `SnapshotHierarchy.set_novel()` never called from Series sources | `load_series_knowledge()` → `merger.set_novel()` for character & glossary |
| **Volume Tier Population** | **UNPOPULATED** — `SnapshotHierarchy.set_volume()` never called | Per-book hydration populates Volume tier from BookMemoryStore |
| **Series Knowledge Persistence** | **NONE** — No `series_knowledge_{series_id}.json` | Deterministic JSON with SHA-256 fingerprint |
| **SeriesManifest Integration** | **MISSING** — No `series_knowledge_hash` field | Add derived field following `series_glossary_hash` pattern |
| **Series Knowledge Loader** | **NONE** — `KnowledgeLoader` only loads from `source` dict | Extend `KnowledgeLoader` with Series domain loading |
| **EntityResolver Integration** | Via MergedRuntime only | Novel tier entries resolved via `MergedRuntime.resolve()` |
| **Cross-Series Isolation** | **NONE** — No series_id in knowledge runtime | Namespace via `series_id` in file path, manifest hash |

---

## 4. Series Knowledge Boundary Definition

### 4.1 Series-Level Authority (Novel Tier — What Belongs to Series)

| Authority | Source | Storage | Strategy |
|-----------|--------|---------|----------|
| **Canonical Character Names** | `SeriesMemoryStore` (FactType.CANONICAL_NAME) | Novel tier: `character` domain | KEY_OVERRIDE |
| **Character Aliases** | `SeriesMemoryStore` (FactType.NAME_VARIANT) | Novel tier: `character` domain | KEY_OVERRIDE |
| **Canonical Relationships** | `SeriesMemoryStore` (FactType.RELATIONSHIP) | Novel tier: `character` domain | KEY_OVERRIDE |
| **Fixed Translations** | `SeriesGlossary` (locked terms) | Novel tier: `glossary` domain | KEY_OVERRIDE |
| **Terminology Preferences** | `SeriesMemoryStore` (FactType.TERMINOLOGY_PREFERENCE) | Novel tier: `glossary` domain | KEY_OVERRIDE |
| **World Facts** | `SeriesMemoryStore` (FactType.OTHER, BACKGROUND) | Novel tier: `general` domain | KEY_OVERRIDE |

### 4.2 Book-Local Scope (Volume Tier — What Remains Book-Local)

| Scope | Source | Storage | Strategy |
|-------|--------|---------|----------|
| **Book-Specific Characters** | `BookMemoryStore` (local facts) | Volume tier: `character` domain | KEY_OVERRIDE (overrides Novel) |
| **Book Glossary Additions** | `BookGlossary` (local terms) | Volume tier: `glossary` domain | KEY_OVERRIDE |
| **Scene/Context State** | `ContextMemoryStore` | Chapter/Chunk tier: `scene`/`narrative` | REPLACE |
| **Style Adaptations** | Per-book style analysis | Volume/Chapter tier: `style` | REPLACE |

### 4.3 Hierarchy Precedence (Frozen — DOMAIN_STRATEGIES)

```
Chunk (highest priority) → Chapter → Volume → Novel (lowest priority)

DOMAIN_STRATEGIES:
- character: KEY_OVERRIDE  (lower level overrides higher for same key)
- glossary: KEY_OVERRIDE
- scene: REPLACE           (lowest non-empty level completely replaces)
- narrative: REPLACE
- style: REPLACE
```

**Critical Rule:** Novel tier provides defaults. Volume tier (book-specific) overrides Novel. Chapter/Chunk override Volume.

---

## 5. Series Knowledge Identity Design

### 5.1 Identity Computation

**File Path:** `output/series/{series_id}/series_knowledge_{series_id}.json`

Namespace isolation achieved via:
- Directory isolation: `output/series/{series_id}/`
- Filename includes `series_id`: `series_knowledge_{series_id}.json`
- Manifest hash: `series_knowledge_hash` in SeriesManifest
- Novel tier keys prefixed with series context implicitly via separate file per series

### 5.2 Knowledge Entry Keys

| Domain | Key Format | Example |
|--------|------------|---------|
| character (canonical name) | `char:{korean_name}` | `char:정태의` → `鄭泰義` |
| character (alias) | `alias:{alias}` | `alias:태의` → `鄭泰義` |
| character (relationship) | `rel:{korean_name}:{relation_type}:{target}` | `rel:정태的:spouse:강나연` |
| glossary | `term:{korean_term}` | `term:정태的` → `鄭泰義` |
| general (world fact) | `fact:{fact_type}:{key}` | `fact:setting:capital_city` |

---

## 6. Cross-Series Isolation — Hard Failure Analysis

| Case | Current Behavior | Required Behavior | Failure Mode |
|------|------------------|-------------------|--------------|
| Same Korean term in Series A and B | Single merged runtime | Different `series_knowledge_{series_id}.json` files | **HARD FAIL** if collision detected |
| Knowledge lookup without explicit SeriesIdentity | Global source dict used | **MUST REQUIRE** explicit `series_id` | **HARD FAIL** if missing |
| Persistence path collision | N/A | `output/series/{series_id}/series_knowledge_{series_id}.json` | **HARD FAIL** if wrong directory |
| Hydration into wrong series book | N/A | Only matching series_id knowledge consulted | **HARD FAIL** if cross-series data used |
| Manifest hash mismatch | N/A | `series_knowledge_hash` validates integrity | **HARD FAIL** on fingerprint mismatch |

**All cases MUST be hard failures.** No silent fallback, no auto-merge.

---

## 7. Series Knowledge Data Model

### 7.1 SeriesKnowledge (Persistence Format)

```python
@dataclass(frozen=True)
class SeriesKnowledge:
    """Series-canonical knowledge for Novel tier population."""
    schema_name: str                         # "ntpe.series_knowledge"
    schema_version: str                      # "1.0"
    series_id: str                           # From SeriesManifest
    character_entries: dict[str, Any]        # char:... / alias:... / rel:...
    glossary_entries: dict[str, Any]         # term:...
    general_entries: dict[str, Any]          # fact:...
    knowledge_hash: str                      # SHA-256 of canonical payload
```

### 7.2 Knowledge Population Report

```python
@dataclass(frozen=True)
class KnowledgePopulationReport:
    """Report of Series → KnowledgeRuntime population."""
    series_id: str
    character_terms_populated: int
    glossary_terms_populated: int
    general_facts_populated: int
    knowledge_hash: str
    source_memory_hash: str
    source_glossary_hash: str
```

---

## 8. Manifest Integration

### 8.1 SeriesManifest Authority Boundary (Per D-03)

| Manifest Field | Authority | SeriesKnowledge Relationship |
|----------------|-----------|----------------------------|
| `series_id` | Manifest (IMMUTABLE) | Knowledge keyed by this |
| `series_name` | Manifest (MUTABLE) | Knowledge references for display |
| `books[]` | Manifest (APPEND-ONLY) | Knowledge tracks provenance |
| `series_memory_hash` | Derived (SeriesMemoryStore) | Independent |
| `series_checkpoint_hash` | Derived (SeriesCheckpoint) | Independent |
| `series_entity_registry_hash` | Derived (SeriesEntityRegistry) | Independent |
| `series_glossary_hash` | Derived (SeriesGlossary) | Independent |
| **NEW: `series_knowledge_hash`** | **Derived (SeriesKnowledge)** | **ADD to manifest** |

### 8.2 Required Manifest Extension

Add to `SeriesManifest` (Batch 5.5 scope — additive, following `series_glossary_hash` pattern):

```python
series_knowledge_hash: str = ""  # DERIVED — SHA256 of SeriesKnowledge payload
```

**Default empty string** for backward compatibility.

### 8.3 Derived-State Boundary (Explicit Contract)

| Property | Requirement |
|----------|-------------|
| **Derived** | `series_knowledge_hash` computed FROM SeriesKnowledge, never reverse |
| **Read-Only from Knowledge** | Knowledge computes hash; Manifest stores it. Knowledge never reads this field for authority. |
| **Never Authority Source** | Manifest field is a fingerprint only. Does not control knowledge content. |
| **Never Overwrites SeriesIdentity** | `series_id`, `series_name`, `created_at` remain Manifest authority. |
| **Never Overwrites Canonical Facts** | Knowledge owns entries. Manifest hash is a checksum only. |

**Data Flow (ONE DIRECTION ONLY):**
```
SeriesKnowledge
    → compute SHA-256 fingerprint (canonical serialization)
    → SeriesKnowledge.get_knowledge_hash()
    → SeriesRegistry.update_series_knowledge_hash(series_id, hash)
    → SeriesManifest.series_knowledge_hash (derived field)
```

**NOT ALLOWED:**
```
SeriesManifest.series_knowledge_hash
    → overwrite SeriesKnowledge  (FORBIDDEN)
    → overwrite SeriesIdentity  (FORBIDDEN)
```

---

## 9. Persistence Design

### 9.1 Artifact Location

```
output/
└── series/
    └── {series_id}/
        ├── series_manifest_{series_id}.json       (Batch 5.1)
        ├── series_memory_{series_id}.json         (Batch 5.2)
        ├── series_entities_{series_id}.json       (Batch 5.3)
        ├── series_glossary_{series_id}.json       (Batch 5.4)
        ├── series_knowledge_{series_id}.json      (Batch 5.5 — NEW)
        └── series_checkpoint_{series_id}.json     (Batch 5.6)
```

### 9.2 Canonical Serialization

```python
def to_canonical_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def compute_series_knowledge_fingerprint(payload: dict) -> str:
    canonical = to_canonical_json({k: v for k, v in payload.items() if k != "knowledge_hash"})
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 9.3 Payload Structure

```json
{
  "schema_name": "ntpe.series_knowledge",
  "schema_version": "1.0",
  "series_id": "a1b2c3d4e5f6g7h8",
  "character_entries": {
    "char:정태的": "鄭泰義",
    "alias:태의": "鄭泰義",
    "rel:정태的:spouse:강나연": "배우자: 강나연"
  },
  "glossary_entries": {
    "term:천마": "天魔",
    "term:무림": "武林"
  },
  "general_entries": {
    "fact:setting:capital": "한양"
  },
  "knowledge_hash": "sha256..."
}
```

### 9.4 Corruption Handling — Fail-Closed

| Scenario | Behavior |
|----------|----------|
| File not found | Return empty knowledge (fresh series) — not error |
| Invalid JSON | `SeriesKnowledgeValidationError` — operation aborted |
| Schema mismatch | `SeriesKnowledgeValidationError` — operation aborted |
| Fingerprint mismatch | `SeriesKnowledgeIntegrityError` — operation aborted |

### 9.5 Atomicity

- Write to temp file → atomic rename (`os.replace`)
- Fingerprint computed before write
- No partial writes visible

---

## 10. Knowledge Population Design

### 10.1 Population Trigger Points

1. **Series Knowledge Build** — After SeriesGlossary built/refreshed (e.g., after book promotion)
2. **Explicit API Call** — `KnowledgeRuntimeManager.load_series_knowledge(series_id)`
3. **Translation Start** — When book translation starts with `series_id`

### 10.2 Population Data Flow

```
SeriesMemoryStore (canonical NEVER facts)
    │
    ├── CANONICAL_NAME → Novel tier: character domain (KEY_OVERRIDE)
    ├── NAME_VARIANT   → Novel tier: character domain (KEY_OVERRIDE)
    ├── RELATIONSHIP   → Novel tier: character domain (KEY_OVERRIDE)
    ├── TERMINOLOGY_PREFERENCE → Novel tier: glossary domain (KEY_OVERRIDE)
    └── BACKGROUND/OTHER → Novel tier: general domain (KEY_OVERRIDE)
    │
SeriesGlossary (locked terms)
    │
    └── locked terms → Novel tier: glossary domain (KEY_OVERRIDE)
    │
    ▼
KnowledgeMerger.set_novel(domain, entries)
    │
    ▼
MergedRuntime (Novel tier populated)
    │
    ├── Resolver queries MergedRuntime
    ├── Book hydration uses Volume tier (BookMemoryStore → set_volume)
    └── Translation uses full hierarchy
```

### 10.3 KnowledgeLoader Extension

```python
# In core/knowledge_runtime/loader.py (EXTENSION - additive)
def load_series_character_knowledge(
    self,
    series_memory_store: SeriesMemoryStore,
) -> Dict[str, Any]:
    """
    Load character canonical facts for Novel tier.
    Returns dict suitable for KnowledgeMerger.set_novel("character", entries).
    """
    entries = {}
    for record in series_memory_store.get_all_canonical_facts():
        if record.fact_type == FactType.CANONICAL_NAME:
            entries[f"char:{record.korean_name}"] = record.canonical_name
            for alias in record.aliases:
                entries[f"alias:{alias}"] = record.canonical_name
        elif record.fact_type == FactType.RELATIONSHIP:
            entries[f"rel:{record.korean_name}:{record.value}"] = record.value
        elif record.fact_type in (FactType.TERMINOLOGY_PREFERENCE, FactType.OTHER, FactType.BACKGROUND):
            entries[f"fact:{record.fact_type.value.lower()}:{record.korean_name}"] = record.value
    return entries

def load_series_glossary_knowledge(
    self,
    series_glossary: SeriesGlossary,
) -> Dict[str, Any]:
    """
    Load locked glossary terms for Novel tier.
    Returns dict suitable for KnowledgeMerger.set_novel("glossary", entries).
    """
    return series_glossary.get_locked_dictionary()
```

### 10.4 KnowledgeRuntimeManager Extension

```python
# In core/knowledge_runtime/manager.py (EXTENSION - additive)
def load_series_knowledge(
    self,
    series_id: str,
    series_memory_store: SeriesMemoryStore,
    series_glossary: SeriesGlossary,
) -> KnowledgePopulationReport:
    """
    Populate Novel tier from Series sources.
    
    Called during Series orchestration before translation.
    """
    self.merger.reset()
    
    # Load character canonical facts → Novel tier
    character_entries = self.loader.load_series_character_knowledge(series_memory_store)
    if character_entries:
        self.merger.set_novel("character", character_entries)
    
    # Load glossary locked terms → Novel tier
    glossary_entries = self.loader.load_series_glossary_knowledge(series_glossary)
    if glossary_entries:
        self.merger.set_novel("glossary", glossary_entries)
    
    # Build merged runtime
    merged_runtime = self.merger.merge_all()
    self._update_resolver_from_merged()
    
    # Compute and persist SeriesKnowledge artifact
    knowledge = SeriesKnowledge(
        schema_name="ntpe.series_knowledge",
        schema_version="1.0",
        series_id=series_id,
        character_entries=character_entries,
        glossary_entries=glossary_entries,
        general_entries={},  # Future extension
        knowledge_hash="",
    )
    fingerprint = compute_series_knowledge_fingerprint(knowledge.to_dict(include_hash=False))
    knowledge = knowledge._replace(knowledge_hash=fingerprint)
    
    # Save to disk
    save_series_knowledge(knowledge, get_series_knowledge_path(self.output_root, series_id))
    
    # Update manifest
    self.series_registry.update_series_knowledge_hash(series_id, fingerprint)
    
    return KnowledgePopulationReport(
        series_id=series_id,
        character_terms_populated=len(character_entries),
        glossary_terms_populated=len(glossary_entries),
        general_facts_populated=0,
        knowledge_hash=fingerprint,
        source_memory_hash=series_memory_store.series_memory_hash,
        source_glossary_hash=series_glossary.glossary_hash,
    )
```

---

## 11. Volume Tier Population (Per Book)

### 11.1 Volume Tier Source

When a book translation starts with `series_id`:
1. BookMemoryStore hydrated from SeriesMemoryStore (Batch 5.2)
2. Book glossary built/hydrated from SeriesGlossary (Batch 5.4)
3. **Volume tier populated** from BookMemoryStore + Book glossary

```python
# In KnowledgeRuntimeManager (additive)
def populate_volume_tier(
    self,
    book_memory_store: MemoryStore,
    book_glossary: dict,
    book_identity: str,
) -> None:
    """
    Populate Volume tier for current book.
    Called at translation start for the specific book.
    """
    # Character facts from BookMemoryStore (includes hydrated series facts)
    volume_character_entries = {}
    for record in book_memory_store.get_all():
        if record.fact_type == FactType.CANONICAL_NAME:
            volume_character_entries[f"char:{record.character_id}"] = record.value
        # ... other fact types
    
    if volume_character_entries:
        self.merger.set_volume("character", volume_character_entries)
    
    # Glossary terms from Book glossary (includes hydrated series terms)
    volume_glossary_entries = {
        f"term:{term}": item["translation"]
        for term, item in book_glossary.items()
        if item.get("translation")
    }
    if volume_glossary_entries:
        self.merger.set_volume("glossary", volume_glossary_entries)
    
    # Re-merge to update MergedRuntime
    self._merged_runtime = self.merger.merge_all()
    self._update_resolver_from_merged()
```

---

## 12. Acceptance Test Matrix for Batch 5.5

| Test ID | Category | Description | Expected Result | Failure Condition |
|---------|----------|-------------|-----------------|-------------------|
| **SK-01** | Novel Tier Population | SeriesMemoryStore facts → Novel tier character domain | Entries present in MergedRuntime | Missing character entries |
| **SK-02** | Novel Tier Population | SeriesGlossary locked terms → Novel tier glossary domain | Locked terms in MergedRuntime | Missing glossary entries |
| **SK-03** | Volume Tier Population | BookMemoryStore → Volume tier | Book facts override Novel | Novel used when Volume exists |
| **SK-04** | Hierarchy Precedence | Chunk > Chapter > Volume > Novel | Lower level wins for KEY_OVERRIDE | Novel used when Volume has entry |
| **SK-05** | Resolver Queries Novel | `resolve_merged(key, "character")` returns series canonical | Canonical name from Series | Returns None or book value |
| **SK-06** | Persistence Integrity | Save → load → fingerprint matches | Hash matches | Fingerprint mismatch |
| **SK-07** | Corruption Rejection | Tampered file → IntegrityError | Exception on load | Load succeeds with corrupted data |
| **SK-08** | Cross-Series Isolation | Series A knowledge not in Series B resolver | No leakage | Cross-series term resolution |
| **SK-09** | Manifest Hash Integration | Knowledge hash stored in SeriesManifest | Hash present and updates | Missing or stale hash |
| **SK-10** | Backward Compatibility | Old manifest (no knowledge hash) loads | Empty string default | Load fails |
| **SK-11** | Provider/Network/Translation | Run all Batch 5.5 tests | 0/0/0 execution | Any external call |
| **SK-12** | Root Hygiene | Check repo root after test run | No new files in root | Files created in root |
| **SK-13** | Frozen Contract Isolation | `core/knowledge_runtime/` core unchanged | Existing tests PASS | Frozen files modified |

---

## 13. Decisions Summary

| Decision | Status | Rationale |
|----------|--------|-----------|
| **Series Knowledge File** | `output/series/{series_id}/series_knowledge_{series_id}.json` | Consistent with SeriesMemory, SeriesEntity, SeriesGlossary patterns |
| **Knowledge Loader Integration** | Extend `core/knowledge_runtime/loader.py` with Series domain loaders | No new module; additive to existing loader |
| **Manager Integration** | Extend `core/knowledge_runtime/manager.py` with `load_series_knowledge()` | Follows existing pipeline: Loader → Merger → Resolver |
| **Novel Tier Source** | SeriesMemoryStore (character) + SeriesGlossary (glossary) | Canonical facts and locked terms are Series-authority |
| **Volume Tier Source** | BookMemoryStore + Book glossary (per book at translation start) | Book-local overrides at Volume level |
| **Persistence** | Deterministic JSON with canonical serialization + SHA-256 | Same pattern as all Series artifacts |
| **Manifest Hash** | Add `series_knowledge_hash` to SeriesManifest | Single source of truth for derived state |
| **Schema Version** | Remains "1.0" (additive derived field) | Follows established pattern |
| **Domain Mapping** | CHARACTER/GLOSSARY/GENERAL domains used for Novel tier | Uses existing KnowledgeDomain enum, no new domains |

---

## 14. Owner Decisions — REQUIRED

The following architectural decisions require Owner confirmation before Batch 5.5 implementation:

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **SK-1: Volume Tier Population Trigger** | At translation start vs explicit API call | **At translation start** (integrated with hydration) |
| **SK-2: General Domain Facts** | Include BACKGROUND/OTHER from SeriesMemoryStore vs character/glossary only | **Include** BACKGROUND/OTHER as `general` domain (future-proof) |
| **SK-3: Knowledge Artifact Schema** | Single file with all domains vs separate files per domain | **Single file** (simpler, consistent with SeriesGlossary) |
| **SK-4: SeriesManifest Extension** | Add `series_knowledge_hash` in Batch 5.5 vs Batch 5.9 | **Batch 5.5** (follows established pattern from 5.1-5.4) |
| **SK-5: EntityResolver Integration** | Via MergedRuntime only (existing) vs direct SeriesKnowledge adapter | **MergedRuntime only** (preserves frozen Resolver contract) |
| **SK-6: KnowledgeDomain Enum** | Add `SERIES` domain vs reuse CHARACTER/GLOSSARY | **Reuse existing domains** (Novel tier is just another layer) |

---

## 15. Blockers

1. **Batch 5.4 must be accepted** (provides `series_id`, `SeriesManifest`, `SeriesRegistry`, `SeriesGlossary`, `series_glossary_hash` primitives)
2. **Owner decisions SK-1 through SK-6 required**
3. **No blocker from existing code** — all changes additive, no frozen contracts modified

---

## 16. Deliverables

1. `docs/governance/rm8/P0_STAGE5_BATCH5_5_PREFLIGHT_AUDIT.md` (this document)
2. `docs/governance/rm8/P0_STAGE5_BATCH5_5_IMPLEMENTATION_TASK.md` (implementation specification — **ONLY if Owner decisions confirmed**)

---

## 17. Validation Results (Preflight)

| Check | Result |
|-------|--------|
| `ntpe_validate.py` | PASS WITH WARNINGS (1 pre-existing warning: optional import) |
| `python -m compileall core/` | PASS (0 errors) |
| `git diff --check` | PASS (clean, only CRLF warnings on pre-existing files) |
| Provider Execution | 0 (audit only) |
| Network Calls | 0 (audit only) |
| Translation Execution | 0 (audit only) |
| Root Hygiene | PASS (no root files created by audit) |
| Production Code Modified | NO (audit only) |

---

## 18. Final Verdict

### Is NTPE Ready for Batch 5.5 Implementation?

> **BLOCKED — Owner Decisions Required (SK-1 ~ SK-6)**

### Blocking Reasons:

1. **Owner Decisions Required** on 6 architectural questions (SK-1 to SK-6)
2. **Batch 5.4 Acceptance Pending** — Series Glossary must be baseline

### Next Steps:

1. Owner reviews and decides on SK-1 ~ SK-6
2. Upon decisions → Update implementation task with confirmed choices
3. Authorize Batch 5.5 implementation

---

*End of Preflight Audit. No production code modified. Awaiting Owner decisions on SK-1 ~ SK-6.*