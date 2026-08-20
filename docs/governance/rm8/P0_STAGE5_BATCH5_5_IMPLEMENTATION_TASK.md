# P0 Stage 5 Batch 5.5 — Series Knowledge Population Implementation Task

**Baseline Commit:** `b13a6ec0df4882a060ba9cf02ed81e2803790a52` (P0 Stage 5 Batch 5.4 Accepted)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` (§3, §9, §11, §24, §25, §28)
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md` (Batch 5.5)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_BATCH5_5_PREFLIGHT_AUDIT.md`
**Task Status:** Specification Defined — Awaiting Owner Decisions (SK-1 ~ SK-6)
**Implementation Status:** NOT STARTED

---

## 1. Objective

Implement the **Series Knowledge Population** for P0 Stage 5 Series Continuity.

**Deliverables:**
- Extensions to `core/knowledge_runtime/loader.py` with Series domain source loaders:
  - `load_series_character_knowledge()` — Load canonical character facts for Novel tier
  - `load_series_glossary_knowledge()` — Load locked glossary terms for Novel tier
- Extension to `core/knowledge_runtime/manager.py`:
  - `load_series_knowledge(series_id, series_memory_store, series_glossary)` — Populate Novel tier from Series sources
  - `populate_volume_tier(book_memory_store, book_glossary, book_identity)` — Populate Volume tier per book
- Deterministic persistence: `series_knowledge_{series_id}.json` with SHA-256 integrity
- SeriesManifest integration via `series_knowledge_hash` derived field (additive to `core/series_identity/manifest.py` and `core/series_identity/registry.py`)
- Hierarchy precedence: Novel (Series) → Volume (Book) → Chapter → Chunk (KEY_OVERRIDE/REPLACE)
- Cross-series isolation via `series_id` namespace
- CSI-04 hard gate for knowledge isolation

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **SeriesKnowledge Model** | Persistent knowledge artifact: `character_entries`, `glossary_entries`, `general_entries`, `knowledge_hash` |
| **KnowledgeLoader Extensions** | `load_series_character_knowledge()`, `load_series_glossary_knowledge()` — additive methods |
| **KnowledgeRuntimeManager Extensions** | `load_series_knowledge()`, `populate_volume_tier()` — additive methods |
| **Persistence** | Deterministic JSON serialization (`series_knowledge_{series_id}.json`) with canonical JSON + SHA-256 fingerprint |
| **Novel Tier Population** | SeriesMemoryStore canonical facts + SeriesGlossary locked terms → `KnowledgeMerger.set_novel()` |
| **Volume Tier Population** | BookMemoryStore + Book glossary → `KnowledgeMerger.set_volume()` (per book at translation start) |
| **Validation & Integrity** | Schema validation, fingerprint verification, fail-closed on corruption |
| **Manifest Integration** | Add `series_knowledge_hash` to `SeriesManifest` (derived field, additive) |
| **Registry Integration** | Add `update_series_knowledge_hash()` to `SeriesRegistry` |
| **Cross-Series Isolation** | Enforce `series_id` namespace in file paths, manifest, and all operations |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| New `core/series_knowledge/` module | Batch Plan: No new module — extend existing `knowledge_runtime/` |
| Modify `core/knowledge_runtime/models.py` | **FROZEN** (KnowledgePrototype, KnowledgeEntry, KnowledgeBundle, KnowledgeSnapshot) |
| Modify `core/knowledge_runtime/merger.py` core logic | **FROZEN** (`KnowledgeMerger`, `DOMAIN_STRATEGIES`, `SnapshotHierarchy`, `MergedKnowledge`, `MergedRuntime`) |
| Modify `core/knowledge_runtime/snapshot.py` | **FROZEN** (`KnowledgeSnapshotStore`, `SnapshotHierarchy`) |
| Modify `core/knowledge_runtime/resolver.py` | **FROZEN** (`KnowledgeResolver` — queries MergedRuntime only) |
| Series Checkpoint Hierarchy | Batch 5.6 |
| Series Orchestration | Batch 5.7 |
| Migration & Compatibility | Batch 5.8 |
| Validation & Freeze | Batch 5.9 |
| Any Provider / Network / Translation execution | Forbidden |
| Feature flag activation | Forbidden |
| Frozen Contract modifications | Forbidden |

---

## 4. Architecture

### 4.1 Module Structure

```
core/knowledge_runtime/
├── __init__.py
├── models.py                 # FROZEN
├── errors.py                 # FROZEN
├── snapshot.py               # FROZEN (SnapshotHierarchy, KnowledgeSnapshotStore)
├── merger.py                 # FROZEN CORE LOGIC (KnowledgeMerger, DOMAIN_STRATEGIES, MergedRuntime)
├── resolver.py               # FROZEN (KnowledgeResolver)
├── loader.py                 # EXTENDED: Series domain loaders
├── manager.py                # EXTENDED: load_series_knowledge(), populate_volume_tier()
```

### 4.2 Dependency / Ownership Diagram

```
SeriesKnowledge (Series-Level Artifact)
    ├── persistence (series_knowledge_{series_id}.json)
    ├── validation (schema, fingerprint, cross-series)
    ├── population (SeriesMemoryStore + SeriesGlossary → Novel tier)
    ├── volume population (BookMemoryStore + BookGlossary → Volume tier)
    ├── canonical serialization + fingerprint
    └── namespace isolation (series_id in path)
    │
    ├── KnowledgeLoader (Lower-Level Producer)
    │   ├── load_series_character_knowledge() → Novel tier character entries
    │   ├── load_series_glossary_knowledge() → Novel tier glossary entries
    │   └── No dependency on SeriesKnowledge internals
    │
    ├── KnowledgeRuntimeManager (Orchestrator)
    │   ├── load_series_knowledge() → coordinates Loader → Merger → Resolver
    │   ├── populate_volume_tier() → per-book Volume tier
    │   ├── persistence via save_series_knowledge()
    │   └── manifest integration via SeriesRegistry
    │
    ├── KnowledgeMerger (FROZEN CORE)
    │   ├── set_novel() — populated by Manager
    │   ├── set_volume() — populated by Manager per book
    │   └── merge_all() → MergedRuntime
    │
    ├── KnowledgeResolver (FROZEN)
    │   └── Queries MergedRuntime exclusively (Novel → Volume → Chapter → Chunk)
    │
    └── SeriesManifest (Authority for derived hash)
        └── series_knowledge_hash (DERIVED, read-only from knowledge perspective)
```

**Forbidden:** Bidirectional dependency `KnowledgeLoader/Manager ↔ SeriesKnowledge` internals

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.series_identity` | Internal | `SeriesManifest`, `SeriesRegistry`, `get_series_dir()` |
| `core.series_memory` | Internal | `SeriesMemoryStore`, `SeriesCharacterRecord`, `FactType` |
| `core.glossary_builder` | Internal | `SeriesGlossary`, `get_locked_dictionary()` |
| `core.knowledge_runtime` (self) | Internal | Existing models, merger, resolver, snapshot |

**No dependencies on:** `core.character_memory_v2`, `core.context_scene_memory`, `core.entity_resolver`, `core.book_intake`, `core.translation_runtime`, `core.runtime_checkpoint`

---

## 5. Data Models

### 5.1 SeriesKnowledge (New — in `core/knowledge_runtime/loader.py` or new `models.py` extension)

```python
@dataclass(frozen=True)
class SeriesKnowledge:
    """Series-canonical knowledge for Novel tier population."""
    schema_name: str                          # "ntpe.series_knowledge"
    schema_version: str                       # "1.0"
    series_id: str                            # From SeriesManifest
    character_entries: dict[str, Any]         # char:..., alias:..., rel:...
    glossary_entries: dict[str, Any]          # term:...
    general_entries: dict[str, Any]           # fact:...
    knowledge_hash: str                       # SHA-256 of canonical payload (excluding hash itself)
```

### 5.2 KnowledgePopulationReport (New)

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

### 5.3 Validation Exceptions (New)

```python
class SeriesKnowledgeValidationError(Exception):
    """Raised when SeriesKnowledge schema validation fails."""
    pass

class SeriesKnowledgeIntegrityError(Exception):
    """Raised when SeriesKnowledge fingerprint verification fails (fail-closed)."""
    pass
```

---

## 6. Series Knowledge Identity Semantics

### 6.1 Namespace Isolation

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_knowledge_{series_id}.json` |
| **Manifest Key** | All operations require explicit `series_id` |
| **Population** | Only knowledge matching `series_id` loaded |
| **Volume Tier** | Per-book, keyed by `book_identity` within Series context |
| **Load Validation** | Payload `series_id` must match directory name |

### 6.2 Knowledge Entry Keys

| Domain | Key Format | Example |
|--------|------------|---------|
| character (canonical name) | `char:{korean_name}` | `char:정태的` → `鄭泰義` |
| character (alias) | `alias:{alias}` | `alias:태의` → `鄭泰義` |
| character (relationship) | `rel:{korean_name}:{relation_type}:{target}` | `rel:정태的:spouse:강나연` |
| glossary | `term:{korean_term}` | `term:천마` → `天魔` |
| general (world fact) | `fact:{fact_type}:{key}` | `fact:setting:capital` → `한양` |

---

## 7. Serialization Rules

### 7.1 Canonical JSON

```python
def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 7.2 Series Knowledge Fingerprint

```python
def compute_series_knowledge_fingerprint(series_knowledge_dict: dict) -> str:
    """Compute SHA-256 of canonical knowledge payload (excluding knowledge_hash itself)."""
    payload = {k: v for k, v in series_knowledge_dict.items() if k != "knowledge_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 7.3 Round-Trip Guarantee

```
series_knowledge → to_canonical_json → bytes → sha256 → knowledge_hash
series_knowledge → to_dict() → load → serialize → same knowledge_hash
```

**Deterministic:** Same inputs → bit-for-bit identical JSON → identical fingerprint.

---

## 8. Validation Rules

### 8.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_knowledge" | `SeriesKnowledgeValidationError` |
| `schema_version` == "1.0" | `SeriesKnowledgeValidationError` |
| `series_id` matches directory/filename | `SeriesKnowledgeValidationError` |
| `knowledge_hash` matches computed | `SeriesKnowledgeIntegrityError` (fail-closed) |
| All entry dicts are `dict[str, Any]` | `SeriesKnowledgeValidationError` |
| No duplicate keys within each domain dict | `SeriesKnowledgeValidationError` |

### 8.2 Business Rule Validation (on Population)

| Operation | Validation |
|-----------|------------|
| `load_series_knowledge()` | SeriesMemoryStore and SeriesGlossary must have matching `series_id` |
| `populate_volume_tier()` | BookMemoryStore must have matching `book_identity` |
| `save_series_knowledge()` | Fingerprint computed before write; atomic rename |

### 8.3 Fail-Closed Principle

- **Any validation failure → Exception**, no partial load, no fallback defaults
- Corrupted knowledge file → `SeriesKnowledgeIntegrityError` → operation blocked
- No silent data corruption

---

## 9. KnowledgeLoader Extensions

### 9.1 `load_series_character_knowledge()`

```python
def load_series_character_knowledge(
    self,
    series_memory_store: SeriesMemoryStore,
) -> Dict[str, Any]:
    """
    Load character canonical facts for Novel tier.
    
    Returns dict suitable for KnowledgeMerger.set_novel("character", entries).
    Only APPROVED NEVER-expiry facts from SeriesMemoryStore.
    """
    entries = {}
    for record in series_memory_store.get_all_canonical_facts():
        # Canonical names
        if record.fact_type == FactType.CANONICAL_NAME:
            entries[f"char:{record.korean_name}"] = record.canonical_name
            for alias in record.aliases:
                entries[f"alias:{alias}"] = record.canonical_name
        # Relationships
        elif record.fact_type == FactType.RELATIONSHIP:
            entries[f"rel:{record.korean_name}:{record.value}"] = record.value
        # Terminology preferences
        elif record.fact_type == FactType.TERMINOLOGY_PREFERENCE:
            entries[f"term:{record.korean_name}"] = record.value
        # World facts / background
        elif record.fact_type in (FactType.BACKGROUND, FactType.OTHER, FactType.PHYSICAL_TRAIT, FactType.PERSONALITY):
            entries[f"fact:{record.fact_type.value.lower()}:{record.korean_name}"] = record.value
    return entries
```

### 9.2 `load_series_glossary_knowledge()`

```python
def load_series_glossary_knowledge(
    self,
    series_glossary: SeriesGlossary,
) -> Dict[str, Any]:
    """
    Load locked glossary terms for Novel tier.
    
    Returns dict suitable for KnowledgeMerger.set_novel("glossary", entries).
    Uses SeriesGlossary.get_locked_dictionary() adapter.
    """
    return series_glossary.get_locked_dictionary()
```

---

## 10. KnowledgeRuntimeManager Extensions

### 10.1 `load_series_knowledge()`

```python
def load_series_knowledge(
    self,
    series_id: str,
    series_memory_store: SeriesMemoryStore,
    series_glossary: SeriesGlossary,
    output_root: Path,
    series_registry: SeriesRegistry,
) -> KnowledgePopulationReport:
    """
    Populate Novel tier from Series sources and persist SeriesKnowledge artifact.
    
    Called during Series orchestration before translation.
    """
    # Validate series_id consistency
    if series_memory_store.series_id != series_id:
        raise SeriesKnowledgeValidationError("SeriesMemoryStore series_id mismatch")
    if series_glossary.series_id != series_id:
        raise SeriesKnowledgeValidationError("SeriesGlossary series_id mismatch")
    
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
    
    # Build SeriesKnowledge artifact
    knowledge = SeriesKnowledge(
        schema_name="ntpe.series_knowledge",
        schema_version="1.0",
        series_id=series_id,
        character_entries=character_entries,
        glossary_entries=glossary_entries,
        general_entries={},  # SK-2: include BACKGROUND/OTHER if Owner confirms
        knowledge_hash="",
    )
    
    fingerprint = compute_series_knowledge_fingerprint(knowledge.to_dict(include_hash=False))
    knowledge = SeriesKnowledge(
        schema_name=knowledge.schema_name,
        schema_version=knowledge.schema_version,
        series_id=knowledge.series_id,
        character_entries=knowledge.character_entries,
        glossary_entries=knowledge.glossary_entries,
        general_entries=knowledge.general_entries,
        knowledge_hash=fingerprint,
    )
    
    # Save to disk
    save_series_knowledge(knowledge, get_series_knowledge_path(output_root, series_id))
    
    # Update manifest
    series_registry.update_series_knowledge_hash(series_id, fingerprint)
    
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

### 10.2 `populate_volume_tier()`

```python
def populate_volume_tier(
    self,
    book_memory_store: MemoryStore,
    book_glossary: dict,
    book_identity: str,
) -> None:
    """
    Populate Volume tier for current book translation.
    
    Called at translation start for the specific book (after Series Novel tier populated).
    Book facts override Novel tier via KEY_OVERRIDE strategy.
    """
    # Character facts from BookMemoryStore (includes hydrated series facts)
    volume_character_entries = {}
    for record in book_memory_store.get_all():
        if record.fact_type == FactType.CANONICAL_NAME:
            # Use book-scoped character_id as key
            volume_character_entries[f"char:{record.character_id}"] = record.value
        elif record.fact_type == FactType.RELATIONSHIP:
            volume_character_entries[f"rel:{record.character_id}:{record.value}"] = record.value
    
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

## 11. Persistence Helpers

### 11.1 File Path

```python
def get_series_knowledge_path(output_root: Path, series_id: str) -> Path:
    """Get the path for series knowledge file."""
    series_dir = output_root / "series" / series_id
    return series_dir / f"series_knowledge_{series_id}.json"
```

### 11.2 Save

```python
def save_series_knowledge(series_knowledge: SeriesKnowledge, path: Path) -> None:
    """Save SeriesKnowledge to disk with atomic write and fingerprint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    data = series_knowledge.to_dict(include_hash=True)
    temp_path.write_text(
        to_canonical_json(data),
        encoding="utf-8"
    )
    temp_path.replace(path)
```

### 11.3 Load

```python
def load_series_knowledge_from_path(path: Path, expected_series_id: str) -> SeriesKnowledge:
    """Load SeriesKnowledge from disk with integrity verification (fail-closed)."""
    if not path.exists():
        # Return empty knowledge for fresh series
        return SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=expected_series_id,
            character_entries={},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SeriesKnowledgeValidationError(f"Invalid JSON in knowledge file: {e}")
    
    # Schema validation
    if data.get("schema_name") != "ntpe.series_knowledge":
        raise SeriesKnowledgeValidationError(f"Invalid schema_name: {data.get('schema_name')}")
    if data.get("schema_version") != "1.0":
        raise SeriesKnowledgeValidationError(f"Invalid schema_version: {data.get('schema_version')}")
    if data.get("series_id") != expected_series_id:
        raise SeriesKnowledgeValidationError(f"Series ID mismatch: expected {expected_series_id}, got {data.get('series_id')}")
    
    # Fingerprint verification (fail-closed)
    stored_hash = data.get("knowledge_hash", "")
    if stored_hash:
        computed_hash = compute_series_knowledge_fingerprint(data)
        if stored_hash != computed_hash:
            raise SeriesKnowledgeIntegrityError(f"Knowledge fingerprint mismatch: stored={stored_hash}, computed={computed_hash}")
    
    return SeriesKnowledge(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        character_entries=data.get("character_entries", {}),
        glossary_entries=data.get("glossary_entries", {}),
        general_entries=data.get("general_entries", {}),
        knowledge_hash=stored_hash,
    )

def load_series_knowledge(series_id: str, output_root: Path) -> SeriesKnowledge:
    """Load SeriesKnowledge from output root with integrity verification."""
    path = get_series_knowledge_path(output_root, series_id)
    return load_series_knowledge_from_path(path, series_id)
```

---

## 12. Manifest Integration

### 12.1 SeriesManifest Extension

Add to `SeriesManifest` (in `core/series_identity/manifest.py` — additive, following existing pattern):

```python
@dataclass(frozen=True)
class SeriesManifest:
    # ... existing fields ...
    series_knowledge_hash: str = field(default="")  # DERIVED — SHA256 of SeriesKnowledge
```

Add `with_series_knowledge_hash()` method:

```python
def with_series_knowledge_hash(self, hash_value: str) -> "SeriesManifest":
    return SeriesManifest(
        schema_name=self.schema_name,
        schema_version=self.schema_version,
        series_id=self.series_id,
        series_name=self.series_name,
        lifecycle_status=self.lifecycle_status,
        created_at=self.created_at,
        updated_at=utc_now_iso(),
        books=self.books,
        series_memory_hash=self.series_memory_hash,
        series_checkpoint_hash=self.series_checkpoint_hash,
        series_entity_registry_hash=self.series_entity_registry_hash,
        series_glossary_hash=self.series_glossary_hash,
        series_knowledge_hash=hash_value,
        manifest_fingerprint="",
    )
```

Update `from_dict()` for backward compatibility:

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "SeriesManifest":
    books = tuple(SeriesBookEntry.from_dict(b) for b in data.get("books", []))
    return cls(
        # ... existing fields ...
        series_knowledge_hash=data.get("series_knowledge_hash", ""),  # Default empty
        # ... existing fields ...
    )
```

### 12.2 SeriesRegistry Extension

Add to `SeriesRegistry` (in `core/series_identity/registry.py`):

```python
def update_series_knowledge_hash(self, series_id: str, knowledge_hash: str) -> SeriesManifest:
    """Update series_knowledge_hash after knowledge changes."""
    manifest = self.get(series_id)
    updated_manifest = manifest.with_series_knowledge_hash(knowledge_hash)
    fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
    updated_manifest = updated_manifest.with_fingerprint(fingerprint)

    series_dir = get_series_dir(self.output_root, series_id)
    manifest_path = manifest_file_path(series_dir, series_id)
    save_manifest(updated_manifest, manifest_path)

    return updated_manifest
```

### 12.3 Derived-State Boundary (Explicit Contract)

| Property | Requirement |
|----------|-------------|
| **Derived** | `series_knowledge_hash` computed FROM SeriesKnowledge, never reverse |
| **Read-Only from Knowledge** | Knowledge computes hash; Manifest stores it. Knowledge never reads this field for authority. |
| **Never Authority Source** | Manifest field is a fingerprint only. Does not control knowledge content. |
| **Never Overwrites SeriesIdentity** | `series_id`, `series_name`, `created_at` remain Manifest authority. |
| **Never Overwrites Canonical Facts** | Knowledge owns entries. Manifest hash is a checksum only. |

---

## 13. Cross-Series Isolation (Hard Enforcement)

### 13.1 Namespace Isolation Rules

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_knowledge_{series_id}.json` |
| **Manifest Key** | All queries require explicit `series_id` |
| **Population** | Only knowledge matching `series_id` loaded |
| **Volume Tier** | Per-book within Series context |
| **Load Validation** | Payload `series_id` must match directory name |

### 13.2 Hard Failure Cases (All MUST Fail)

| Case | Validation Point |
|------|------------------|
| Load knowledge with mismatched `series_id` | `load_series_knowledge_from_path()` |
| Populate Novel tier for wrong series | `load_series_knowledge()` |
| Populate Volume tier for book of different series | `populate_volume_tier()` |
| File path collision | Impossible — directory隔离 |

---

## 14. CSI-04 Acceptance Tests (Hard Gates)

> **All MUST PASS. Any failure → Batch 5.5 not accepted.**

| Test ID | Description | Verification |
|---------|-------------|--------------|
| **CSI-04** | Series A knowledge ≠ Series B | Verify file naming `series_knowledge_{series_id}.json` and manifest hash isolation |
| **SK-01** | Novel tier populated from SeriesMemoryStore | Character canonical names in MergedRuntime |
| **SK-02** | Novel tier populated from SeriesGlossary | Locked glossary terms in MergedRuntime |
| **SK-03** | Volume tier per book overrides Novel | Book facts take precedence over Series |
| **SK-04** | Hierarchy precedence: Chunk > Chapter > Volume > Novel | KEY_OVERRIDE for character/glossary, REPLACE for scene/narrative/style |
| **SK-05** | Resolver queries Novel tier via MergedRuntime | `resolve_merged()` returns Series canonical |
| **SK-06** | Persistence integrity: save → load → hash matches | Hash matches |
| **SK-07** | Corruption rejection: tampered fingerprint → IntegrityError | Fail-closed on load |
| **SK-08** | Cross-series isolation: Series A knowledge → Series B resolver | No leakage |
| **SK-09** | Manifest hash integration: knowledge hash in SeriesManifest | Hash present, updates on knowledge change |
| **SK-10** | Backward compat: old manifest loads | Empty string default |
| **SK-11** | Provider/Network/Translation = 0/0/0 | Verified in test runs |
| **SK-12** | Root hygiene: no files in repo root | Git status clean |
| **SK-13** | Frozen contract isolation: knowledge_runtime core unchanged | Existing tests PASS |

---

## 15. Frozen Contracts Audit

**Batch 5.5 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | No touch |
| Context Pipeline Contract | No touch |
| Prompt Pipeline Contract | No touch |
| Plugin Contract | No touch |
| Production Pipeline Contract | No touch |
| Translation Runtime Contract | No touch |
| Intelligence Contract | No touch |
| **Knowledge Contract** | **FROZEN** — Core models, merger, resolver, snapshot unchanged |
| Snapshot Contract | No touch |
| Character Memory v2 core | No touch |
| Context/Scene Memory core | No touch |
| Entity Resolver core | No touch |
| Runtime Checkpoint core | No touch |
| All 9 Foundation Frozen Contracts | No touch |

**New Contract Created by Batch 5.5:**
- **Series Knowledge Contract** (extensions to `core/knowledge_runtime/loader.py` and `manager.py`) — to be added to Foundation Manifest in Batch 5.9

---

## 16. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/knowledge_runtime/models.py` | **FROZEN** |
| `core/knowledge_runtime/merger.py` | **FROZEN CORE LOGIC** |
| `core/knowledge_runtime/snapshot.py` | **FROZEN** |
| `core/knowledge_runtime/resolver.py` | **FROZEN** |
| `core/knowledge_runtime/errors.py` | **FROZEN** |
| `core/character_memory_v2/` | **FROZEN** |
| `core/context_scene_memory/` | **FROZEN** |
| `core/entity_resolver/` | **FROZEN** |
| `core/book_intake/` | **FROZEN** |
| `core/translation_runtime/` | **FROZEN** |
| `core/translation_pipeline/` | **FROZEN** |
| `core/production_runtime/` | **FROZEN** |
| `core/runtime_checkpoint/` | **FROZEN** |
| Any Frozen Contract (9 existing) | **FROZEN** |
| Feature flag changes | **FROZEN** |
| TXT/EPUB/Translation behavior | **FROZEN** |
| Provider/Network/Translation execution | **FROZEN** |

---

## 17. Test Requirements

### 17.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_series_knowledge_creation` | Create knowledge with all domains |
| `test_series_knowledge_serialization_roundtrip` | Save → load → fingerprint matches |
| `test_series_knowledge_fingerprint_integrity` | Tampered file → IntegrityError |
| `test_load_series_character_knowledge` | SeriesMemoryStore → Novel tier entries |
| `test_load_series_glossary_knowledge` | SeriesGlossary → Novel tier entries |
| `test_load_series_knowledge_populates_novel` | Merger Novel tier populated |
| `test_populate_volume_tier_overrides_novel` | Book facts override Series facts |
| `test_hierarchy_precedence_key_override` | Volume overrides Novel for same key |
| `test_hierarchy_precedence_replace` | Volume replaces Novel for REPLACE domains |
| `test_resolver_queries_novel_tier` | MergedRuntime resolves Series canonical |
| `test_namespace_isolation` | Series A knowledge not in Series B |
| `test_persistence_roundtrip` | Save → load → fingerprint matches |
| `test_persistence_corrupted_fail_closed` | Corrupted file → IntegrityError |
| `test_deterministic_serialization` | Same knowledge → bit-for-bit identical JSON |
| `test_manifest_hash_integration` | Knowledge hash stored in SeriesManifest |
| `test_manifest_hash_updates` | Manifest fingerprint changes with knowledge |
| `test_old_manifest_loads` | Pre-Batch 5.5 manifest loads with empty hash |

### 17.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_knowledge_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |
| `test_novel_tier_deterministic` | 1000 |

### 17.3 Cross-Series Isolation Tests (CSI-04)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_04_knowledge_file_isolation` | CSI-04 |
| `test_csi_04_resolver_isolation` | CSI-04 |

### 17.4 Integration Tests

| Test | Description |
|------|-------------|
| `test_series_knowledge_in_book2_translation` | Book 1 promote → Book 2 populate → Series canonical resolved |
| `test_cross_series_no_leakage_knowledge` | Series A knowledge not in Series B book |
| `test_volume_tier_priority` | Book-specific term overrides Series canonical |

---

## 18. Batch 5.5 Acceptance Test Matrix (Comprehensive)

| Category | Test | Description | Pass Criteria |
|----------|------|-------------|---------------|
| **Persistence** | `test_persist_save_load` | Save knowledge, load, verify fingerprint | Fingerprint matches, entries intact |
| **Persistence** | `test_persist_corrupted_fail_closed` | Corrupt JSON, attempt load | `SeriesKnowledgeIntegrityError` raised |
| **Persistence** | `test_persist_missing_file` | Load non-existent knowledge | Empty SeriesKnowledge |
| **Persistence** | `test_persist_restart` | Process restart simulation | Reload produces identical state |
| **Reload** | `test_reload_idempotent` | Load → save → load → save | Bit-for-bit identical JSON |
| **Population** | `test_novel_tier_character` | SeriesMemoryStore → Novel character domain | Canonical names + aliases present |
| **Population** | `test_novel_tier_glossary` | SeriesGlossary → Novel glossary domain | Locked terms present |
| **Population** | `test_novel_tier_relationships` | SeriesMemoryStore RELATIONSHIP → Novel | Relationship entries present |
| **Volume Tier** | `test_volume_overrides_novel` | Book fact overrides Series canonical | Book value in MergedRuntime |
| **Volume Tier** | `test_volume_adds_new` | Book adds new term not in Series | New term in Volume tier |
| **Resolver** | `test_resolve_novel_character` | Query Series canonical via MergedRuntime | Correct target returned |
| **Resolver** | `test_resolve_volume_override` | Query book override via MergedRuntime | Book value returned |
| **Resolver** | `test_resolve_fallback_chain` | Chunk→Chapter→Volume→Novel chain | Correct precedence |
| **Cross-Series** | `test_isolation_same_character` | Series A "정태的" vs Series B "正泰的" | Different files, no leakage |
| **Cross-Series** | `test_isolation_promotion_gated` | Populate Series A, verify Series B clean | Series B unaffected |
| **Corruption** | `test_corruption_fingerprint` | Tamper fingerprint | IntegrityError on load |
| **Corruption** | `test_corruption_json` | Malformed JSON | ValidationError on load |
| **Corruption** | `test_corruption_schema` | Wrong schema_name/version | ValidationError on load |
| **Deterministic** | `test_deterministic_json` | Same knowledge, multiple serializations | Bit-for-bit identical |
| **Deterministic** | `test_deterministic_hash` | Same knowledge, multiple hashes | Identical SHA-256 |
| **Backward Compat** | `test_compat_no_series_id` | KnowledgeRuntime without series_id works | Works identically to baseline |
| **Fail-Closed** | `test_fail_closed_all_paths` | All validation paths throw exceptions | No fallback defaults |

---

## 19. Validation Gates

**All must PASS before Batch 5.5 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-04 + SK-01~13 tests PASS
- [ ] Batch 5.5 Acceptance Test Matrix (§18) all PASS
- [ ] No regression in existing pytest tests (KnowledgeRuntime, Series Identity, Series Memory, Series Entity, Series Glossary)
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 20. Git Scope Rules

**Allowed Changes:**

- **ADDITIVE** `core/knowledge_runtime/loader.py` — Two new methods, new dataclasses, new exceptions, persistence helpers
- **ADDITIVE** `core/knowledge_runtime/manager.py` — Two new methods
- **ADDITIVE** `core/series_identity/manifest.py` — Add `series_knowledge_hash` derived field (following `series_glossary_hash` pattern)
- **ADDITIVE** `core/series_identity/registry.py` — Add `update_series_knowledge_hash()` method
- **NEW** `tests/series/test_batch5_5_*.py` (test files)

**Forbidden:**

- Any modification to existing production code outside allowed additive changes
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 21. Delivery Rules

**Deliverables (working tree changes only, no staging):**

1. Extended `core/knowledge_runtime/loader.py` with Series knowledge loaders
2. Extended `core/knowledge_runtime/manager.py` with population methods
3. Additive changes to `core/series_identity/manifest.py` — `series_knowledge_hash` derived field
4. Additive changes to `core/series_identity/registry.py` — `update_series_knowledge_hash()` method
5. `tests/series/test_batch5_5_*.py`
6. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 22. Rollback Boundary

**Clean Rollback:**

- Revert `core/knowledge_runtime/loader.py` to baseline
- Revert `core/knowledge_runtime/manager.py` to baseline
- Revert `core/series_identity/manifest.py` to baseline
- Revert `core/series_identity/registry.py` to baseline
- Delete `tests/series/test_batch5_5_*.py`

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules
- **Frozen knowledge_runtime core files UNCHANGED — no revert needed**

---

## 23. Provider / Network / Translation Policy

- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation only

---

## 24. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/knowledge_runtime/loader.py` — implementation (extended)
- `core/knowledge_runtime/manager.py` — implementation (extended)
- `core/series_identity/manifest.py` — additive manifest field
- `core/series_identity/registry.py` — additive registry method
- `tests/series/` — tests
- `docs/governance/rm8/` — docs
- `artifacts/` — diagnostic output only

---

## 25. Completion Criteria

**Batch 5.5 Complete When:**

1. All §17 unit tests PASS
2. All §17 property-based tests PASS (1000 iterations each)
3. All §17 CSI-04 + SK-01~13 tests PASS
4. All §18 Batch 5.5 Acceptance Test Matrix PASS
5. Validation gates (§19) all PASS
6. Git status shows only allowed new files + allowed additive changes
7. No production code modified outside allowed additive changes
8. No Frozen Contracts modified
9. **Frozen knowledge_runtime core unchanged** (models.py, merger.py, snapshot.py, resolver.py, errors.py)

**Status Report:** "P0 Stage 5 Batch 5.5 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 26. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Preflight complete, models defined, integration points specified, Owner decisions pending | 2026-08-20 |
| Owner | SK-1 ~ SK-6 decisions confirmed; Authorization to proceed | ____________ |
| QA | CSI-04 + SK-01~13 test matrix & Acceptance Test Matrix accepted | ____________ |

---

## 27. Owner Decisions — PENDING (To Be Confirmed)

| Decision | Options | Pending Choice |
|----------|---------|----------------|
| **SK-1: Volume Tier Population Trigger** | At translation start vs explicit API call | **PENDING** |
| **SK-2: General Domain Facts** | Include BACKGROUND/OTHER vs character/glossary only | **PENDING** |
| **SK-3: Knowledge Artifact Schema** | Single file vs separate files per domain | **PENDING** |
| **SK-4: SeriesManifest Extension** | Add `series_knowledge_hash` in Batch 5.5 vs Batch 5.9 | **PENDING** |
| **SK-5: EntityResolver Integration** | MergedRuntime only vs direct adapter | **PENDING** |
| **SK-6: KnowledgeDomain Enum** | Add SERIES domain vs reuse CHARACTER/GLOSSARY | **PENDING** |

---

*End of Batch 5.5 Implementation Task. Specification DEFINED — Awaiting Owner Decisions (SK-1 ~ SK-6) for Implementation Authorization.*