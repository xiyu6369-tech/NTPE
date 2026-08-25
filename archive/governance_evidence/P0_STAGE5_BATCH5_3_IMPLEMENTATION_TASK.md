# P0 Stage 5 Batch 5.3 — Series Entity Registry Implementation Task

**Baseline Commit:** `25704fbab53eeb2cef2a69b933c3c347bca1d9c1` (P0 Stage 5 Batch 5.2 Accepted)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` (§6, §8.1, §9, §10, §13, §20, §24, §25)
**Amendment:** `docs/governance/rm8/P0_STAGE5_SPECIFICATION_AMENDMENT.md`
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md` (Batch 5.3)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_BATCH5_3_SERIES_ENTITY_PREFLIGHT_AUDIT.md`
**Task Status:** Specification Complete — Ready for Owner Authorization
**Implementation Status:** NOT STARTED

---

## 1. Objective

Implement the **Series Entity Registry** for P0 Stage 5 Series Continuity.

**Deliverables:**
- `core/series_entity_registry/` module (models, registry, persistence, integration, validation)
- `SeriesEntityRecord` — persistent canonical entity mappings per series
- `SeriesEntityRegistry` — CRUD, query, hydration, promotion, persistence
- Deterministic persistence with SHA-256 integrity (`series_entities_{series_id}.json`)
- EntityResolver integration with SERIES precedence (USER level)
- Namespace isolation via `series_entity_id = sentity_{sha256(series_id|source|type)[:16]}`
- MANUAL promotion gate (D-07 frozen)
- CSI-02 cross-series isolation hard gates

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **SeriesEntityRecord Model** | Canonical entity mapping: `series_entity_id`, `source_name`, `canonical_target`, `entity_type`, `source_level=USER`, `metadata`, `approved_at`, `approved_by`, `version` |
| **SeriesEntityRegistry** | `register()`, `get()`, `get_by_source()`, `get_all()`, `update_target()`, `promote_from_resolver()`, `hydrate_resolver()`, `validate_integrity()` |
| **Persistence** | Deterministic JSON (`series_entities_{series_id}.json`) with canonical serialization + SHA-256 fingerprint |
| **EntityResolver Integration** | Add optional `series_registry` parameter; check series registry BEFORE RUNTIME in `_resolve_single()` |
| **Hydration (Series → Book)** | Project SeriesEntityRegistry entries into `EntityResolver.user_overrides` at USER level |
| **Promotion (Book → Series)** | MANUAL approval-gated promotion of USER overrides from resolver to registry; conflict detection |
| **Validation & Conflict Detection** | Schema validation, fingerprint verification, duplicate ID collision detection, cross-series isolation validation |
| **Manifest Integration** | Add `series_entity_registry_hash` to `SeriesManifest` (derived field) |
| **Cross-Series Isolation** | Enforce `series_id` namespace in all IDs, file paths, and operations |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Redesign Entity Resolver core | **FROZEN** (Constraint) |
| Redesign Entity Normalization (RM-7.3) | **FROZEN** — global registry remains for non-series use |
| Redesign Entity Review / Consistency | **FROZEN** |
| Series Glossary | Batch 5.4 |
| Series Knowledge Population | Batch 5.5 |
| Series Checkpoint Hierarchy | Batch 5.6 |
| Series Orchestration / Coordinator | Batch 5.7 |
| Migration & Compatibility | Batch 5.8 |
| Validation & Freeze | Batch 5.9 |
| Any Provider / Network / Translation execution | Forbidden |
| Feature flag activation | Forbidden |
| Frozen Contract modifications | Forbidden |

---

## 4. Architecture

### 4.1 Module Structure

```
core/series_entity_registry/
├── __init__.py                    # Public exports
├── models.py                      # SeriesEntityRecord, EntityPromotionRecord
├── registry.py                    # SeriesEntityRegistry (CRUD, hydration, promotion)
├── persistence.py                 # Load/save series_entities_{series_id}.json
├── integration.py                 # EntityResolver integration helpers
└── validation.py                  # Registry validation, conflict detection, fingerprint
```

### 4.2 Dependency / Ownership Diagram

```
SeriesEntityRegistry (Series-Level Owner)
    ├── persistence
    ├── validation
    ├── promotion (Book → Series, MANUAL gate)
    ├── hydration (Series → Book, read-only)
    ├── namespace isolation (series_entity_id)
    └── canonical serialization
    │
    └── EntityResolver (Lower-Level Consumer) — FROZEN CORE
        ├── Receives hydrated user_overrides via EXISTING extension point
        ├── Generates promotion candidates from user_overrides (additive)
        ├── No dependency on SeriesEntityRegistry internals
        └── Core _resolve_single logic UNCHANGED (no modification)
```

**Forbidden:** Bidirectional dependency `EntityResolver ↔ SeriesEntityRegistry`

**EntityResolver Integration Boundary (Exact):**

The ONLY authorized integration point is the existing `user_overrides: Dict[str, str]` parameter in `EntityResolver.__init__()`.

Batch 5.3 integration works as follows:
1. `SeriesEntityRegistry.hydrate_resolver()` builds a `user_overrides` dict from all `SeriesEntityRecord` entries
2. This dict is passed to `EntityResolver(user_overrides=...)` at resolver construction time
3. The frozen `_resolve_single()` logic already checks `user_overrides` FIRST (USER level precedence)
4. No modification to `EntityResolver` class, `_resolve_single()`, or precedence semantics
5. No modification to `EntityResolver` models (`ResolvedEntity`, `EntityInjectionSet`, `InjectionSource`, `EntityType`)
6. No modification to `EntityResolver` lifecycle methods

This is an **additive adapter pattern** — SeriesEntityRegistry produces a dict compatible with the existing extension point.

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.entity_resolver.models` | Internal | `EntityType`, `InjectionSource`, `ResolvedEntity` (read-only) |
| `core.entity_resolver.resolver` | Internal | `EntityResolver` (additive integration only) |
| `core.series_identity` | Internal | `SeriesIdentity`, `SeriesManifest`, `SeriesRegistry` (read-only) |
| `core.series_memory` | Internal | `SeriesMemoryStore` (for cross-reference, read-only) |

**No dependencies on:** `core.character_memory_v2`, `core.context_scene_memory`, `core.knowledge_runtime`, `core.book_intake`, `core.translation_runtime`, `core.runtime_checkpoint`

---

## 5. Data Models

### 5.1 SeriesEntityRecord (Canonical Entity Mapping)

```python
@dataclass(frozen=True)
class SeriesEntityRecord:
    """Persistent canonical entity mapping — series-scoped, USER-level authority."""
    series_entity_id: str           # sentity_{sha256(series_id|source_name|entity_type)[:16]}
    source_name: str                # Korean source (e.g., "정태의")
    canonical_target: str           # Approved Chinese (e.g., "鄭泰義")
    entity_type: EntityType         # CHARACTER, PLACE, TERMINOLOGY, ORGANIZATION
    source_level: InjectionSource   # Always USER for series registry
    metadata: Dict[str, Any]        # Provenance: source_books, book_coverage, etc.
    approved_at: str                # ISO timestamp of this version
    approved_by: str                # "user" or "series_promotion"
    version: int                    # Starts at 1, increments on update
```

**Field Authority Summary:**

| Field | Authority | Mutability |
|-------|-----------|------------|
| `series_entity_id` | Creation | **IMMUTABLE** |
| `source_name` | Creation | **IMMUTABLE** |
| `canonical_target` | User/Promotion | **MUTABLE** (via SUPERSEDED → version++) |
| `entity_type` | Creation | **IMMUTABLE** |
| `source_level` | Contract | **IMMUTABLE** (always USER) |
| `metadata` | System/User | **APPEND-ONLY** (add provenance) |
| `approved_at` | System | **IMMUTABLE** per version |
| `approved_by` | System/User | **IMMUTABLE** per version |
| `version` | System | **AUTO-INCREMENT** |

**Key Differences from RM-7.3 CanonicalEntity:**
- `series_entity_id` instead of `entity_id` (namespace isolated)
- `source_level` always `USER` (series registry = persistent USER override)
- `metadata` tracks `source_books` across volumes
- `version` for audit trail on supersession
- No `name_forms` — surface forms handled by EntityNormalization (separate integration)

---

### 5.2 EntityPromotionRecord (Audit Trail)

```python
@dataclass(frozen=True)
class EntityPromotionRecord:
    """Audit trail for Book → Series entity promotion."""
    promotion_id: str
    series_id: str
    book_identity: str
    source_name: str
    entity_type: EntityType
    previous_target: str | None
    new_target: str
    action: str                     # "created" | "no_op" | "conflict"
    resolved_by: str | None         # "user" | None (for conflict)
    resolved_at: str
    source_level: str               # "USER_OVERRIDE" | "LEARNING"
```

---

### 5.3 SeriesEntityRegistry Operations

| Operation | Description |
|-----------|-------------|
| `register(record: SeriesEntityRecord) -> AddResult` | Add or merge canonical entity; conflict detection |
| `get(series_entity_id: str) -> SeriesEntityRecord \| None` | Get by namespace-isolated ID |
| `get_by_source(source_name: str, entity_type: EntityType) -> SeriesEntityRecord \| None` | Get by source + type (typed query) |
| `get_all() -> Tuple[SeriesEntityRecord, ...]` | Get all entities (sorted by ID) |
| `get_by_type(entity_type: EntityType) -> Tuple[SeriesEntityRecord, ...]` | Filter by entity type |
| `update_target(series_entity_id: str, new_target: str, approved_by: str) -> AddResult` | Supersede canonical target (version++) |
| `hydrate_resolver(resolver: EntityResolver, book_identity: str, registry_hash: str) -> HydrationReport` | Inject all records as USER overrides |
| `promote_from_resolver(resolver: EntityResolver, book_identity: str, approval_gate: bool = True) -> Tuple[AddResult, ...]` | Promote USER overrides from resolver |
| `validate_integrity() -> bool` | Verify fingerprint matches |
| `get_registry_hash() -> str` | Compute SHA-256 for Manifest integration |

---

## 6. Series Entity ID Semantics

### 6.1 Identity Computation

```python
def compute_series_entity_id(series_id: str, source_name: str, entity_type: str) -> str:
    """
    Namespace-isolated entity ID for Series Entity Registry.
    
    Canonicalization:
    - source_name: strip whitespace, preserve Unicode
    - entity_type: uppercase (CHARACTER, PLACE, TERMINOLOGY, ORGANIZATION)
    """
    canonical_source = source_name.strip()
    canonical_type = entity_type.upper()
    return f"sentity_{hashlib.sha256(f'{series_id}|{canonical_source}|{canonical_type}'.encode()).hexdigest()[:16]}"
```

**Properties:**
- Same `(series_id, source_name, entity_type)` → same `series_entity_id` (deterministic, cross-machine)
- `series_entity_id` **never changes** after creation
- Different `series_id` → different `series_entity_id` (isolation)
- Different `entity_type` → different `series_entity_id` (type-aware)

### 6.2 Entity Type Mapping (Owner Decision SE-1)

**Decision: Use RM-7.2 EntityType set** — `CHARACTER`, `PLACE`, `ORGANIZATION`, `TERMINOLOGY`, `UNKNOWN`

```python
# In integration.py — map between resolver and registry types
RESOLVER_TO_REGISTRY_TYPE = {
    "CHARACTER": EntityType.CHARACTER,
    "PLACE": EntityType.PLACE,
    "ORGANIZATION": EntityType.ORGANIZATION,
    "TERMINOLOGY": EntityType.TERMINOLOGY,
    "TERM": EntityType.TERMINOLOGY,
    "UNKNOWN": EntityType.TERMINOLOGY,
}
```

---

## 7. Serialization Rules

### 7.1 Canonical JSON

```python
def to_canonical_json(obj: dict[str, Any]) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 7.2 Registry Fingerprint

```python
def compute_series_entity_registry_fingerprint(registry_dict: dict[str, Any]) -> str:
    """Compute SHA-256 of canonical registry payload (excluding fingerprint itself)."""
    payload = {k: v for k, v in registry_dict.items() if k != "series_entity_registry_fingerprint"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 7.3 Round-Trip Guarantee

```
registry → to_canonical_json → bytes → sha256 → fingerprint
registry → to_dict() → load → serialize → same fingerprint
```

**Deterministic:** Same inputs → bit-for-bit identical JSON → identical fingerprint.

---

## 8. Validation Rules

### 8.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_entity_registry" | `SeriesEntityValidationError` |
| `schema_version` == "1.0" | `SeriesEntityValidationError` |
| `series_id` matches directory/filename | `SeriesEntityValidationError` |
| `series_entity_registry_fingerprint` matches computed | `SeriesEntityIntegrityError` (fail-closed) |
| All required fields present per record | `SeriesEntityValidationError` |
| `series_entity_id` matches computed `compute_series_entity_id()` | `SeriesEntityValidationError` |
| `source_level` == `InjectionSource.USER.value` | `SeriesEntityValidationError` |
| `version` >= 1 | `SeriesEntityValidationError` |
| `approved_at`, `approved_at` valid ISO 8601 UTC | `SeriesEntityValidationError` |
| No duplicate `series_entity_id` | `SeriesEntityValidationError` |

### 8.2 Business Rule Validation (on Mutations)

| Operation | Validation |
|-----------|------------|
| `register(record)` | Record must be USER level; ID matches computed; no ID collision with different data |
| `update_target(id, new_target)` | Record exists; new_target != current; version increments |
| `hydrate_resolver(resolver, book_identity, registry_hash)` | Registry hash matches current; book_identity in SeriesManifest |
| `promote_from_resolver(resolver, book_identity, approval_gate)` | `approval_gate=True` enforced; only USER_OVERRIDE source_level promoted |

### 8.3 Fail-Closed Principle

- **Any validation failure → Exception**, no partial load, no fallback defaults
- Corrupted registry file → `SeriesEntityIntegrityError` → operation aborted
- No silent data corruption

---

## 9. Hydration Rules (Series → Book) — Read-Only Projection

### 9.1 Hydration Trigger

- At EntityResolver initialization for book (when `series_id` provided)
- At explicit `SeriesEntityRegistry.hydrate_resolver()` call

### 9.2 Hydration Data Flow

```
SeriesEntityRegistry (all SeriesEntityRecord)
    │
    ├── For each record:
    │     resolver.user_overrides[record.source_name] = record.canonical_target
    │
    ▼
EntityResolver._resolve_single():
    1. USER override (existing in-memory)
    2. SERIES REGISTRY (NEW - hydrated user_overrides)
    3. RUNTIME
    4. LEARNING
    5. AUTO
```

### 9.3 Hydration Field Matrix

| Series Field | Resolver Field | Allowed? | Reason |
|--------------|----------------|----------|--------|
| `source_name` | `user_overrides` key | ✅ YES | Canonical identity source |
| `canonical_target` | `user_overrides` value | ✅ YES | Approved translation |
| `entity_type` | Metadata (for extractor) | ✅ YES | Entity type for extraction |
| `metadata.source_books` | Provenance tracking | ✅ YES | Cross-book provenance |
| `approved_by`, `approved_at` | Audit metadata | ✅ YES | Traceability |

### 9.4 Hydration Conflict Resolution

| Resolver State | Series Record | Action |
|----------------|---------------|--------|
| No user_override for source | Any | Create override |
| Existing user_override, SAME target | Any | NO-OP |
| Existing user_override, DIFFERENT target | Series record | **CONFLICT** — log, keep resolver override (book-local wins for session) |

**Note:** Hydration does NOT overwrite existing in-memory user_overrides. Conflicts are logged for user awareness.

### 9.5 Hydration Idempotency

- Hydration is **idempotent** — re-running produces same `user_overrides`
- Uses `series_entity_registry_hash` in SeriesManifest to detect changes
- Resolver tracks `hydration_source = f"series:{series_id}:{registry_hash}"`

---

## 10. Promotion Rules (Book → Series) — MANUAL Gate

### 10.1 Promotion Boundary (CRITICAL)

**Series owns canonical entity mappings. Book proposes. Promotion requires MANUAL approval.**

### 10.2 Promotion Logic

```python
def promote_from_resolver(
    self,
    resolver: EntityResolver,
    book_identity: str,
    approval_gate: bool = True,
) -> Tuple[AddResult, ...]:
    """
    Promote USER overrides from EntityResolver to SeriesEntityRegistry.
    
    Requires MANUAL approval gate (frozen by D-07).
    Only USER_OVERRIDE source_level promoted.
    Conflict: SAME target → NO-OP, DIFFERENT target → CONFLICT.
    """
    if approval_gate is False:
        raise SeriesEntityValidationError(
            "Entity promotion requires MANUAL approval gate (D-07 frozen). "
            "Auto-promotion is not permitted."
        )
    
    results = []
    for source_name, target in resolver.user_overrides.items():
        # Determine entity_type from resolver metadata or default
        entity_type = self._infer_entity_type(resolver, source_name)
        
        series_entity_id = compute_series_entity_id(self.series_id, source_name, entity_type)
        existing = self.get(series_entity_id)
        
        if existing is None:
            # CREATE new
            record = SeriesEntityRecord(
                series_entity_id=series_entity_id,
                source_name=source_name,
                canonical_target=target,
                entity_type=entity_type,
                source_level=InjectionSource.USER,
                metadata={"source_books": [book_identity], "book_coverage": 1},
                approved_at=utc_now_iso(),
                approved_by="series_promotion",
                version=1,
            )
            self.register(record)
            action = "created"
        elif existing.canonical_target == target:
            # NO-OP
            action = "no_op"
        else:
            # CONFLICT
            action = "conflict"
            # Create conflict record, don't modify existing
        
        # Create promotion record
        promotion = EntityPromotionRecord(...)
        self._promotion_records.append(promotion)
        results.append(AddResult(...))
    
    return tuple(results)
```

### 10.3 Promotion Policy (Fixed — Not Configurable)

```python
@dataclass(frozen=True)
class EntityPromotionPolicy:
    auto_promote_user_overrides: bool = False      # MANUAL only (D-07)
    auto_promote_learning: bool = False            # NEVER
    conflict_resolution: str = "manual"            # "manual" only
    require_user_approval: bool = True             # Always True
```

**No auto-promotion.** All promotions require explicit user action. Policy is frozen.

### 10.4 Conflict Resolution (Manual)

| Conflict Type | Resolution Options |
|---------------|-------------------|
| Different canonical_target for same source+type | User chooses: "book_wins", "series_wins", or "manual" (new value) |
| Duplicate promotion attempt | Idempotent — returns existing record |

---

## 11. Manifest Integration

### 11.1 SeriesManifest Extension

Add to `SeriesManifest` (in `core/series_identity/manifest.py` — additive, following existing `series_memory_hash`/`series_checkpoint_hash` pattern):

```python
@dataclass(frozen=True)
class SeriesManifest:
    # ... existing fields ...
    series_entity_registry_hash: str = ""  # DERIVED — SHA256 of SeriesEntityRegistry
```

**Add supporting method (following existing pattern):**

```python
def with_series_entity_registry_hash(self, hash_value: str) -> "SeriesManifest":
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
        series_entity_registry_hash=hash_value,
        manifest_fingerprint="",
    )
```

**Update `from_dict` for backward compatibility (fail-closed for pre-Batch 5.3 manifests):**

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "SeriesManifest":
    books = tuple(SeriesBookEntry.from_dict(b) for b in data.get("books", []))
    return cls(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        series_name=data["series_name"],
        lifecycle_status=SeriesLifecycle(data["lifecycle_status"]),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        books=books,
        series_memory_hash=data.get("series_memory_hash", ""),
        series_checkpoint_hash=data.get("series_checkpoint_hash", ""),
        series_entity_registry_hash=data.get("series_entity_registry_hash", ""),  # Default empty for old manifests
        manifest_fingerprint=data.get("manifest_fingerprint", ""),
    )
```

### 11.2 Registry Hash Update (SeriesRegistry method)

```python
def update_series_entity_registry_hash(self, series_id: str, registry_hash: str) -> SeriesManifest:
    """Update series_entity_registry_hash after registry changes."""
    manifest = self.get(series_id)
    updated_manifest = manifest.with_series_entity_registry_hash(registry_hash)
    fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
    updated_manifest = updated_manifest.with_fingerprint(fingerprint)
    series_dir = get_series_dir(self.output_root, series_id)
    manifest_path = manifest_file_path(series_dir, series_id)
    save_manifest(updated_manifest, manifest_path)
    return updated_manifest
```

### 11.3 Derived-State Boundary (Explicit Contract)

| Property | Requirement |
|----------|-------------|
| **Derived** | `series_entity_registry_hash` is computed FROM SeriesEntityRegistry, never the reverse |
| **Read-Only from Registry** | Registry computes hash; Manifest stores it. Registry never reads this field for authority. |
| **Never Authority Source** | Manifest field is a fingerprint only. Does not control registry content. |
| **Never Overwrites SeriesIdentity** | `series_id`, `series_name`, `created_at` remain Manifest authority. |
| **Never Overwrites Canonical Entity Records** | Registry owns `SeriesEntityRecord` content. Manifest hash is a checksum only. |

**Data Flow (ONE DIRECTION ONLY):**

```
SeriesEntityRegistry
    → compute SHA-256 fingerprint (canonical serialization)
    → SeriesEntityRegistry.get_registry_hash()
    → SeriesRegistry.update_series_entity_registry_hash(series_id, hash)
    → SeriesManifest.series_entity_registry_hash (derived field)
```

**NOT ALLOWED:**
```
SeriesManifest.series_entity_registry_hash
    → overwrite SeriesEntityRegistry  (FORBIDDEN)
    → overwrite SeriesIdentity        (FORBIDDEN)
    → overwrite SeriesEntityRecord    (FORBIDDEN)
```

### 11.4 Schema Version Handling

| Aspect | Decision |
|--------|----------|
| `schema_version` | **UNCHANGED** — remains `"1.0"`. Adding a derived field with default empty string is backward-compatible, not a schema break. |
| `schema_name` | **UNCHANGED** — remains `"ntpe.series_manifest"` |

**Rationale:** The `series_memory_hash` and `series_checkpoint_hash` fields were added in Batch 5.1/5.2 with the same `"1.0"` schema version. This follows the established pattern: derived fields use default empty string in `from_dict`, making old manifests loadable without version bump.

### 11.5 Canonical Serialization & Manifest Fingerprint

- **Canonical dict includes the new field** — `to_canonical_dict()` returns all fields except `manifest_fingerprint`, including `series_entity_registry_hash`
- **Fingerprint changes when registry hash changes** — This is EXPECTED behavior for derived fields (same as `series_memory_hash` and `series_checkpoint_hash`)
- **Deterministic** — Same registry state → same manifest fingerprint

```python
def to_canonical_dict(self) -> dict[str, Any]:
    return self.to_dict(include_manifest_fingerprint=False)
    # Includes: schema_name, schema_version, series_id, series_name,
    # lifecycle_status, created_at, updated_at, books,
    # series_memory_hash, series_checkpoint_hash, series_entity_registry_hash
```

### 11.6 Backward Compatibility / Fail-Closed Behavior

| Scenario | Behavior |
|----------|----------|
| Load pre-Batch 5.3 manifest (no `series_entity_registry_hash` field) | `from_dict` uses `.get("series_entity_registry_hash", "")` → empty string. Load succeeds. |
| Load manifest with empty `series_entity_registry_hash` | Treated as "registry not yet initialized" — valid state. |
| Registry hash computed but manifest not yet updated | Manifest fingerprint will mismatch on next load → `IntegrityError` (fail-closed). Caller must call `update_series_entity_registry_hash()` after registry changes. |
| Corrupted manifest (fingerprint mismatch) | `IntegrityError` — fail-closed, no partial load. |

**Fail-Closed Principle:** Any fingerprint mismatch → exception. No silent fallback.

### 11.7 Batch 5.3 Modification Scope

**Batch 5.3 IS PERMITTED to modify `SeriesManifest`** for this derived field addition because:
1. Follows established pattern from Batch 5.1/5.2 (`series_memory_hash`, `series_checkpoint_hash`)
2. Additive only — new field with default empty string
3. No schema version bump required
4. Backward compatible via `.get()` with default
5. No authority boundary violation — field is derived, read-only from registry perspective

**No additive compatibility mechanism needed** — the existing `from_dict` pattern with `.get(field, "")` handles it.

### 11.8 Authority Boundary

- Manifest owns: `series_id`, `series_name`, `books[]`, `lifecycle_status`, `created_at`, `updated_at`
- Registry owns: `SeriesEntityRecord` content, `series_entity_registry_hash` (computed)
- Registry **never** writes to Manifest authority fields
- Registry reads `series_id` from Manifest for namespace validation
- Manifest stores registry's derived fingerprint as integrity checkpoint

---

## 12. Cross-Series Isolation (Hard Enforcement)

### 12.1 Namespace Isolation Rules

| Layer | Mechanism |
|-------|-----------|
| **Entity ID** | `series_entity_id = sentity_{sha256(series_id|source|type)[:16]}` |
| **File Path** | `output/series/{series_id}/series_entities_{series_id}.json` |
| **Registry Key** | All queries require explicit `series_id` |
| **Hydration** | Only registry matching `series_id` consulted |
| **Promotion** | Only resolver from matching `series_id` book promoted |
| **Load Validation** | Payload `series_id` must match directory name |

### 12.2 Hard Failure Cases (All MUST Fail)

| Case | Validation Point |
|------|------------------|
| Load registry with mismatched `series_id` | `persistence.py` load |
| Register record with wrong `series_id` in ID | `validation.py` register |
| Hydrate resolver from wrong series registry | `registry.hydrate_resolver()` |
| Promote from resolver of different series | `registry.promote_from_resolver()` |
| File path collision (same filename, different series) | Impossible — directory隔离 |

---

## 13. CSI-02 Acceptance Tests (Hard Gates)

> **All MUST PASS. Any failure → Batch 5.3 not accepted.**

| Test ID | Description | Verification |
|---------|-------------|--------------|
| **CSI-02** | Same entity name in Series A vs B → different `series_entity_id` | Verify `compute_series_entity_id()` uses `series_id` prefix |
| **SE-01** | Deterministic identity: same inputs → same `series_entity_id` | 1000 iterations property test |
| **SE-03** | Same-series resolution: register → get_by_source returns correct target | Unit test |
| **SE-04** | Cross-series isolation: Series A entity not visible in Series B registry | Independent registries |
| **SE-05** | Persistence isolation: Series A file ≠ Series B file | File paths include series_id |
| **SE-06** | Hydration isolation: Series A registry → Book B resolver = no entities | Hydration checks series_id |
| **SE-07** | Promotion MANUAL gate: `approval_gate=False` raises exception | Exception on auto-promote |
| **SE-08** | Conflict detection: different target → CONFLICT disposition | AddResult.disposition == "conflict" |
| **SE-09** | Corruption rejection: tampered fingerprint → IntegrityError | Fail-closed on load |
| **SE-10** | Restart continuity: save → load → hydrate → same state | Integration test |
| **SE-11** | Lifecycle: supersede increments version, archive blocks writes | Version++, read-only after archive |
| **SE-12** | Frozen contract isolation: EntityResolver core unchanged | Existing tests PASS, only additive integration |
| **SE-13** | Provider/Network/Translation = 0/0/0 | Verified in test runs |
| **SE-14** | Root hygiene: no files in repo root | Git status clean |
| **SE-15** | Entity type isolation: same source, different type → different ID | Type in hash input |

---

## 14. Frozen Contracts Audit

**Batch 5.3 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | No touch |
| Context Pipeline Contract | No touch |
| Prompt Pipeline Contract | No touch |
| Plugin Contract | No touch |
| Production Pipeline Contract | No touch |
| Translation Runtime Contract | No touch |
| Intelligence Contract | No touch |
| Knowledge Contract | No touch |
| Snapshot Contract | No touch |
| Character Memory v2 core | No touch |
| Context/Scene Memory core | No touch |
| Entity Resolver core (`models.py`, `injector.py`, `_resolve_single` logic) | **Only additive: optional `series_registry` param** |
| KnowledgeRuntime core | No touch |
| Runtime Checkpoint core | No touch |

**New Contract Created by Batch 5.3:**
- **Series Entity Contract** (`core/series_entity_registry/`) — to be added to Foundation Manifest in Batch 5.9

---

## 15. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/entity_resolver/models.py` | **FROZEN** |
| `core/entity_resolver/injector.py` | **FROZEN** |
| `core/entity_resolver/resolver.py` | **FROZEN** — NO modifications (not even additive parameters) |
| `core/entity_normalization/` | **FROZEN** (global registry deprecated for series) |
| `core/entity_review/` | **FROZEN** |
| `core/entity_consistency/` | **FROZEN** |
| `core/character_memory_v2/` | **FROZEN** |
| `core/context_scene_memory/` | **FROZEN** |
| `core/knowledge_runtime/` | **FROZEN** |
| `core/book_intake/` | **FROZEN** |
| `core/translation_runtime/` | **FROZEN** |
| `core/translation_pipeline/` | **FROZEN** |
| `core/production_runtime/` | **FROZEN** |
| `core/runtime_checkpoint/` | **FROZEN** |
| Any Frozen Contract (9 existing) | **FROZEN** |
| Feature flag changes | **FROZEN** |
| TXT/EPUB/Translation behavior | **FROZEN** |
| Provider/Network/Translation execution | **FROZEN** |

**EntityResolver Integration Boundary (Authorized):**
- EXISTING `user_overrides: Dict[str, str]` parameter in `EntityResolver.__init__()` — frozen since RM-7.2
- `SeriesEntityRegistry.hydrate_resolver()` produces compatible `Dict[str, str]`
- Caller injects via `EntityResolver(user_overrides=..., ...)` — no resolver modification
- Precedence USER > RUNTIME > LEARNING > AUTO preserved (frozen in `_resolve_single()`)

---

## 16. Test Requirements

### 16.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_compute_series_entity_id_deterministic` | Same (series_id, source, type) → same ID |
| `test_compute_series_entity_id_namespace_isolation` | Different series_id → different ID |
| `test_compute_series_entity_id_type_aware` | Same source, different type → different ID |
| `test_series_entity_record_immutability` | ID, source, type immutable after creation |
| `test_series_entity_record_source_level_enforced` | Only USER source_level allowed |
| `test_series_entity_registry_crud` | Create, read, update (supersede), list |
| `test_series_entity_registry_deduplication` | Same entity → ACCEPTED first, NO-OP second |
| `test_series_entity_registry_conflict_detection` | Different target → CONFLICT |
| `test_hydration_resolver_injection` | Registry entries → resolver.user_overrides |
| `test_hydration_idempotent` | Hydrate twice → same resolver state |
| `test_hydration_conflict_resolver_wins` | Existing resolver override preserved |
| `test_promotion_manual_gate` | MANUAL approval required; auto-promotion blocked |
| `test_promotion_new_entity` | New USER override → created in registry |
| `test_promotion_same_target` | Same target → NO-OP |
| `test_promotion_conflict` | Different target → CONFLICT |
| `test_namespace_isolation` | Series A "正泰" ≠ Series B "正泰" |
| `test_persistence_roundtrip` | Save → load → fingerprint matches |
| `test_persistence_integrity` | Tampered file → IntegrityError |
| `test_persistence_fail_closed` | Corrupted JSON → exception |
| `test_deterministic_serialization` | Same records → bit-for-bit identical JSON |
| `test_promotion_audit_trail` | EntityPromotionRecord created for each action |
| `test_manifest_hash_integration` | Registry hash stored in SeriesManifest |

### 16.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_entity_id_deterministic_property` | 1000 |
| `test_series_entity_registry_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |
| `test_hydration_idempotent_property` | 1000 |

### 16.3 Cross-Series Isolation Tests (CSI-02)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_02_series_entity_id_isolation` | CSI-02 |

### 16.4 Integration Tests

| Test | Description |
|------|-------------|
| `test_resolver_precedence_series_over_runtime` | SERIES > RUNTIME > LEARNING > AUTO |
| `test_book2_hydration_from_book1_promotion` | Book 1 promote → Book 2 hydrate → canonical names present |
| `test_cross_series_no_leakage_resolver` | Series A resolver overrides not in Series B |

---

## 17. Batch 5.3 Acceptance Test Matrix (Comprehensive)

| Category | Test | Description | Pass Criteria |
|----------|------|-------------|---------------|
| **Persistence** | `test_persist_save_load` | Save registry, load, verify fingerprint | Fingerprint matches, records intact |
| **Persistence** | `test_persist_corrupted_fail_closed` | Corrupt JSON, attempt load | `SeriesEntityIntegrityError` raised |
| **Persistence** | `test_persist_missing_file` | Load non-existent registry | Empty registry (not error) |
| **Persistence** | `test_persist_restart` | Process restart simulation | Reload produces identical state |
| **Reload** | `test_reload_idempotent` | Load → save → load → save | Bit-for-bit identical JSON |
| **Promotion** | `test_promote_new_override` | Promote new USER override from Book 1 | SeriesEntityRecord created |
| **Promotion** | `test_promote_same_target` | Promote override with same target as series | NO-OP, no duplicate |
| **Promotion** | `test_promote_conflict` | Promote override with different target | CONFLICT, requires MANUAL |
| **Promotion** | `test_promote_learning_blocked` | Attempt promote LEARNING data | Blocked, not promoted |
| **Approval Gate** | `test_approval_manual_only` | Verify no auto-promotion path exists | All promotions require user action |
| **Approval Gate** | `test_approval_audit_trail` | Verify EntityPromotionRecord created | Complete audit trail |
| **Conflict Handling** | `test_conflict_detection` | Different canonical_target for same source | Conflict detected, no silent overwrite |
| **Conflict Handling** | `test_conflict_resolution_manual` | User resolves conflict, series updated | Series updated, audit trail recorded |
| **Hydration** | `test_hydrate_user_overrides` | Series entities → resolver.user_overrides | All records injected at USER level |
| **Hydration** | `test_hydrate_idempotent` | Hydrate twice | Identical resolver.user_overrides |
| **Hydration** | `test_hydrate_resolver_conflict` | Resolver has different override | Resolver override preserved, conflict logged |
| **Cross-Series Isolation** | `test_isolation_same_source` | Series A "정태의" vs Series B "정泰" | Different series_entity_id, no leakage |
| **Cross-Series Isolation** | `test_isolation_promotion_gated` | Promote in Series A, verify Series B clean | Series B unaffected |
| **Cross-Series Isolation** | `test_isolation_filesystem` | Delete Series A dir, Series B intact | No cross-directory references |
| **Corruption** | `test_corruption_fingerprint` | Tamper fingerprint | IntegrityError on load |
| **Corruption** | `test_corruption_json` | Malformed JSON | ValidationError on load |
| **Corruption** | `test_corruption_schema` | Wrong schema_name/version | ValidationError on load |
| **Deterministic Serialization** | `test_deterministic_json` | Same records, multiple serializations | Bit-for-bit identical |
| **Deterministic Serialization** | `test_deterministic_hash` | Same records, multiple hashes | Identical SHA-256 |
| **Process Restart** | `test_restart_continuity` | Simulate restart, reload registry | Canonical entities available for Book 2 |
| **Frozen Contract** | `test_resolver_core_unchanged` | Existing EntityResolver tests PASS | No regression |
| **Fail-Closed** | `test_fail_closed_all_paths` | All validation paths throw exceptions | No fallback defaults |

---

## 18. Validation Gates

**All must PASS before Batch 5.3 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-02 + SE-01~15 tests PASS
- [ ] Batch 5.3 Acceptance Test Matrix (§17) all PASS
- [ ] No regression in existing pytest tests (EntityResolver, EntityNormalization, Series Identity, Series Memory)
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 19. Git Scope Rules

**Allowed Changes:**

- **NEW** `core/series_entity_registry/` (complete module)
- **NEW** `tests/series/test_batch5_3_*.py` (test files)
- **ADDITIVE** `core/series_identity/manifest.py` — Add `series_entity_registry_hash` derived field (following `series_memory_hash` pattern)
- **ADDITIVE** `core/series_identity/registry.py` — Add `update_series_entity_registry_hash()` method

**EntityResolver Integration:** NO FILE MODIFICATIONS.
- Uses EXISTING `user_overrides` parameter in `EntityResolver.__init__()` — authorized extension point
- `SeriesEntityRegistry.hydrate_resolver()` returns `Dict[str, str]` for `user_overrides`
- Caller constructs `EntityResolver(user_overrides=hydrated_overrides, ...)` — additive usage only
- No changes to `core/entity_resolver/resolver.py`, `extractor.py`, or `__init__.py`

**Forbidden:**

- Any modification to existing production code outside allowed additive changes
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 20. Delivery Rules

**Deliverables (working tree changes only, no staging):**

1. `core/series_entity_registry/` module
2. `tests/series/test_batch5_3_*.py`
3. Additive changes to `core/series_identity/manifest.py` — `series_entity_registry_hash` derived field
4. Additive changes to `core/series_identity/registry.py` — `update_series_entity_registry_hash()` method
5. Updated `P0_STAGE5_FORMAL_SPECIFICATION.md` (if any spec clarifications needed)
6. This Implementation Task document (as record)

**EntityResolver Integration:** NO FILE MODIFICATIONS.
- Uses EXISTING `user_overrides` parameter in `EntityResolver.__init__()`
- `SeriesEntityRegistry.hydrate_resolver()` returns `Dict[str, str]` compatible with existing extension point
- Caller responsibility: `EntityResolver(user_overrides=registry.hydrate_resolver(...), ...)`
- No changes to `core/entity_resolver/` files

**No staging, no commit, no push, no tag.**

---

## 21. Rollback Boundary

**Clean Rollback:**

- Delete `core/series_entity_registry/` directory
- Revert `core/series_identity/manifest.py` to baseline
- Revert `core/series_identity/registry.py` to baseline

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules
- **EntityResolver files UNCHANGED — no revert needed**

---

## 22. Provider / Network / Translation Policy

- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation only

---

## 23. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/series_entity_registry/` — implementation
- `tests/series/` — tests
- `core/entity_resolver/` — additive integration
- `core/series_identity/` — additive manifest/registry fields
- `docs/governance/rm8/` — docs/contracts
- `artifacts/` — diagnostic output only

---

## 24. Completion Criteria

**Batch 5.3 Complete When:**

1. All §16 unit tests PASS
2. All §16 property-based tests PASS (1000 iterations each)
3. All §16 CSI-02 + SE-01~15 tests PASS
4. All §17 Batch 5.3 Acceptance Test Matrix PASS
5. Validation gates (§18) all PASS
6. Git status shows only allowed new files + allowed additive changes
7. No production code modified outside allowed additive changes
8. No Frozen Contracts modified
9. **EntityResolver core logic unchanged** (only additive series_registry parameter)

**Status Report:** "P0 Stage 5 Batch 5.3 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 25. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Preflight complete, models defined, integration points specified, Owner decisions incorporated | 2026-08-19 |
| Owner | Authorization to proceed | ____________ |
| QA | CSI-02 + SE-01~15 test matrix & Acceptance Test Matrix accepted | ____________ |

---

## 26. Owner Decisions — FROZEN (Owner Confirmed 2026-08-20)

All decisions below are **OWNER-CONFIRMED and FROZEN** for Batch 5.3 implementation.

| Decision | Options | FROZEN Choice |
|----------|---------|---------------|
| **SE-1: Entity Type Set** | RM-7.2 (CHARACTER, PLACE, ORGANIZATION, TERMINOLOGY, UNKNOWN) vs RM-7.3 (CHARACTER, LOCATION, ORGANIZATION, TERM) | **RM-7.2 set** — FROZEN |
| **SE-2: Name Forms in Registry** | Full EntityNameForms vs canonical_target only | **Minimal — canonical_target only** — FROZEN |
| **SE-3: Registry Query API** | `get_by_source(source)` vs `get_by_source(source, entity_type)` | **Typed query — require entity_type** — FROZEN |
| **SE-4: EntityResolver Integration Boundary** | (a) Modify EntityResolver core (b) Use EXISTING user_overrides extension point (c) Defer to Batch 5.7 | **Option (b) — Use EXISTING user_overrides extension point only** — FROZEN. EntityResolver core remains UNCHANGED. |
| **SE-5: Version Granularity** | Per-record version vs registry-level version | **Per-record version** — FROZEN |

---

*End of Batch 5.3 Implementation Task. Specification FINALIZED — Ready for Implementation Authorization.*