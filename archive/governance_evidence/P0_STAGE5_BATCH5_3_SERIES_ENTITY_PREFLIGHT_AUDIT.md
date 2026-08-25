# P0 Stage 5 Batch 5.3 — Series Entity Registry Preflight Audit

**Baseline Commit:** `25704fbab53eeb2cef2a69b933c3c347bca1d9c1` (P0 Stage 5 Batch 5.2 Accepted)
**Audit Date:** 2026-08-19
**Status:** Preflight Audit — No Production Code Modified

---

## 1. Executive Summary

This audit examines NTPE's current entity architecture to establish the preflight analysis for **P0 Stage 5 Batch 5.3 — Series Entity Registry**. The baseline includes:

- **Batch 5.1** (Series Identity & Manifest): `core/series_identity/` — `SeriesIdentity`, `SeriesManifest`, `SeriesRegistry`, deterministic `series_id`, cross-series isolation primitives (CSI-01~10)
- **Batch 5.2** (Series Memory Store): `core/series_memory/` — `SeriesMemoryStore`, `SeriesCharacterRecord`, `SeriesFactRecord`, `SeriesNamespaceMapping`, hydration (Series→Book), promotion (Book→Series with MANUAL gate), persistence

**Primary Finding:** NTPE has **entity resolution and normalization capabilities** at book scope but **no persistent Series-level entity registry**. The existing EntityResolver (RM-7.2) uses in-memory `user_overrides` and `learning_data` dicts that are lost on process exit. EntityNormalization (RM-7.3) uses a global in-memory `EntityIdentityRegistry` singleton with no series namespace isolation.

Batch 5.3 must establish:
- `SeriesEntityRecord` — persistent canonical entity mappings per series
- `SeriesEntityRegistry` — CRUD, query, persistence, EntityResolver integration
- Namespace isolation via `series_entity_id = sentity_{sha256(series_id|source|type)[:16]}`
- EntityResolver precedence: SERIES (USER level) > RUNTIME > LEARNING > AUTO
- Deterministic persistence with SHA-256 integrity

---

## 2. Existing Capability Inventory

### 2.1 Entity Resolver (RM-7.2) — `core/entity_resolver/`

| Component | Status | Details |
|-----------|--------|---------|
| **EntityResolver Class** | Complete | `resolve()`, `_resolve_single()`, precedence USER→RUNTIME→LEARNING→AUTO |
| **Models** | Complete | `ResolvedEntity`, `EntityInjectionSet`, `ExtractedEntity`, `EntityType`, `InjectionSource`, `UNKNOWN_TRANSLATION` |
| **User Overrides** | In-Memory Only | `user_overrides: Dict[str, str]` — lost on process exit |
| **Learning Data** | In-Memory Only | `learning_data: Dict[str, str]` — confidence ≥0.8, lost on exit |
| **Runtime Integration** | Complete | Queries `MergedRuntime` domains (character, glossary, scene, narrative) |
| **Persistence** | **NONE** | No file persistence for overrides/learning |
| **Series Scope** | **NONE** | Per-book resolver only |
| **Extractor** | Complete | `ExtractedEntity` extraction from text chunks |
| **Injector** | Complete | Prompt injection of resolved entities |

**Key Limitation:** User overrides are session-scoped. No mechanism to persist canonical entity mappings across books or sessions.

---

### 2.2 Entity Normalization (RM-7.3) — `core/entity_normalization/`

| Component | Status | Details |
|-----------|--------|---------|
| **Models** | Complete | `CanonicalEntity`, `EntityNameForms`, `NameFormTranslation`, `NameFormType`, `EntityType`, `ConflictRecord`, `NormalizationContext`, `NormalizedEntity`, `NormalizationResult` |
| **Identity Registry** | Global Singleton | `EntityIdentityRegistry` (in-memory), `get_identity_registry()`, `register_entity()`, `resolve_entity()` |
| **Entity ID Generation** | MD5-based | `generate_entity_id(entity_type, source_name)` → `{type}_{md5[:8]}` e.g. `character_a1b2c3d4` |
| **Surface Forms** | Complete | FULL_NAME, GIVEN_NAME, FAMILY_NAME, NICKNAME, TITLE, FORMAL, INTIMATE, RELATIONSHIP |
| **Name Form Classification** | Complete | `classify_name_form()`, `resolve_name_form()`, `build_normalized_entity()` |
| **Context-Aware Resolution** | Complete | `NormalizationContext` with speaker, listener, relationship hints |
| **Series Namespace Isolation** | **NONE** | Global registry, no series_id prefix |
| **Persistence** | **NONE** | In-memory only |

**Key Limitation:** No namespace isolation — same Korean name in Series A and Series B collides in global registry.

---

### 2.3 Entity Review & Consistency — `core/entity_review/`, `core/entity_consistency/`

| Component | Status | Details |
|-----------|--------|---------|
| **ReviewCandidate** | Complete | Generated from consistency mismatches, lifecycle OPEN→ACCEPTED→REJECTED |
| **KnowledgeEvolutionCandidate** | Complete | Bridge to KE after ACCEPTED, preserves provenance |
| **EntityMismatch** | Complete | Mismatch between expected/actual translation |
| **ConsistencyReport** | Complete | Aggregated scan results |
| **Series Scope** | **NONE** | Per-book only |

---

### 2.4 Series Identity (Batch 5.1) — `core/series_identity/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesIdentity** | Complete | `series_id` (immutable, SHA256), `series_name` (mutable), timestamps |
| **SeriesManifest** | Complete | Books with volume_number, book_identity, status, fingerprints |
| **SeriesRegistry** | Complete | `create()`, `get()`, `list_all()`, `add_book()`, `update_name()`, `archive()` |
| **Persistence** | Complete | `output/series/{series_id}/series_manifest_{series_id}.json` |
| **Canonical JSON + Fingerprint** | Complete | Deterministic serialization, SHA-256 manifest_fingerprint |
| **Fail-Closed Validation** | Complete | Schema validation, hash verification, IntegrityError on corruption |
| **Cross-Series Isolation (D-08, D-09)** | Complete | Different `series_id` = complete isolation; same `series_name` allowed, no auto-merge |

**Delivered Primitives for Downstream:**
- `compute_series_id(user_defined_series_key)` — deterministic
- `series_id` as namespace prefix for all downstream IDs
- `SeriesManifest` as single source of truth for series identity/membership

---

### 2.5 Series Memory Store (Batch 5.2) — `core/series_memory/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesCharacterRecord** | Complete | Canonical NEVER-expiry facts, `series_character_id = schar_{sha256(series_id|korean)[:16]}` |
| **SeriesFactRecord** | Complete | Non-character canonical facts, `series_fact_id = sfact_{sha256(series_id|type|value)[:16]}` |
| **SeriesMemoryStore** | Complete | CRUD, `get_canonical_name()`, `get_relationships()`, `get_all_canonical_facts()` |
| **Hydration (Series→Book)** | Complete | Conservative scope: only APPROVED NEVER-expiry fact types |
| **Promotion (Book→Series)** | Complete | MANUAL gate (D-07 frozen), conflict detection, audit trail |
| **Namespace Mapping** | Complete | `SeriesNamespaceMapping`: `korean_to_series_id`, `series_id_to_book_ids`, collision validation |
| **Persistence** | Complete | `output/series/{series_id}/series_memory_{series_id}.json` with fingerprint |
| **Character Memory v2 Integration** | Additive | Optional `series_id` param in `load_or_create_character_memory()`, hydration call |

**Delivered Primitives for Downstream:**
- `series_character_id` namespace isolation contract (CSI-01)
- Hydration/promotion patterns with conflict handling
- Per-series persistence with integrity

---

## 3. Existing Entity Architecture — Gap Analysis

| Capability | Current State | Required for Batch 5.3 |
|------------|---------------|------------------------|
| **Entity Resolver** | RM-7.2 complete, in-memory overrides only | Add SeriesEntityRegistry as persistent USER-level source |
| **Entity Registry** | Global in-memory singleton (RM-7.3) | Replace with Series-scoped persistent registry |
| **Book-Scoped Entity Records** | ResolvedEntity (per-chunk) | Remain book-local; Series provides canonical source |
| **Canonical Entity Records** | CanonicalEntity (RM-7.3, in-memory) | SeriesEntityRecord (persistent, series-scoped) |
| **Alias/Variant Mapping** | EntityNameForms (RM-7.3) | Part of SeriesEntityRecord via metadata/name_forms |
| **Entity Persistence** | None (in-memory only) | `series_entities_{series_id}.json` with fingerprint |
| **Entity Conflict Detection** | RM-7.3 ConflictRecord (in-memory) | SeriesEntityRegistry must detect cross-book conflicts |
| **Entity Namespace Isolation** | None (global registry) | `series_entity_id` with series_id prefix (CSI-02) |
| **Cross-Series Isolation** | Failed (preflight §9) | Enforced by series_id namespace prefix |
| **Series→Book Hydration** | SeriesMemoryStore only | SeriesEntityRegistry → EntityResolver.user_overrides |
| **Book→Series Promotion** | SeriesMemoryStore only | USER overrides from book → SeriesEntityRegistry |

---

## 4. Series Entity Registry Boundary Definition

### 4.1 Series-Level Authority (What Belongs to Series)

| Authority | Description | Storage |
|-----------|-------------|---------|
| **Canonical Entity Mappings** | Korean source → Approved Chinese target per entity type | `SeriesEntityRecord` in `SeriesEntityRegistry` |
| **USER Overrides** | Persistent user-approved translations (highest priority) | `source_level = InjectionSource.USER` |
| **Cross-Book Entity Identity** | Same entity across volumes maps to same canonical target | `series_entity_id` namespace-isolated |
| **Entity Metadata** | Provenance (source_books), approval timestamp, approver | `SeriesEntityRecord.metadata` |
| **Alias/Variant Groups** | All known surface forms for an entity | Via EntityNormalization integration (future) |

### 4.2 Book-Local Scope (What Remains Book-Local)

| Scope | Description | Storage |
|-------|-------------|---------|
| **Transient Resolution** | Per-chunk entity extraction + resolution | `EntityResolver` runtime |
| **Learning Patterns** | Historical auto-learned mappings (confidence-based) | `learning_data` dict (in-memory) |
| **Scene/Chapter Entity State** | Context-dependent forms (speaker, intimacy) | `ContextMemoryStore`, `NormalizationContext` |
| **Temporary Inference** | AI_INFERENCE evidence, unapproved candidates | `EntityReview` candidates (OPEN status) |
| **Book-Local Overrides** | Session-specific user corrections | `user_overrides` dict (in-memory) |

### 4.3 Hydration & Promotion Boundary (Re-Use Batch 5.2 Policy)

| Direction | Policy | Implementation |
|-----------|--------|----------------|
| **Series → Book (Hydration)** | **Read-only projection** | SeriesEntityRegistry entries injected into EntityResolver as `user_overrides` at USER level |
| **Book → Series (Promotion)** | **MANUAL approval gate** (D-07 frozen) | APPROVED user_overrides from book translation promoted via explicit user action |
| **Conflict Detection** | **Hard failure** | Different canonical target for same source → CONFLICT, requires MANUAL resolution |

**Critical Rule:** No reverse uncontrolled writes. Series never receives automatic writes from book runtime.

---

## 5. Series Entity Identity Design

### 5.1 Identity Computation (Per Formal Spec §6.2, §8.1)

```python
def compute_series_entity_id(series_id: str, source_name: str, entity_type: str) -> str:
    """
    Namespace-isolated entity ID for Series Entity Registry.
    
    Format: sentity_{sha256(series_id|source_name|entity_type)[:16]}
    """
    import hashlib
    return f"sentity_{hashlib.sha256(f'{series_id}|{source_name}|{entity_type}'.encode()).hexdigest()[:16]}"
```

### 5.2 Identity Properties

| Property | Behavior |
|----------|----------|
| **Deterministic** | Same `(series_id, source_name, entity_type)` → same `series_entity_id` (cross-machine, cross-run) |
| **Immutable** | `series_entity_id` never changes after creation |
| **Namespace Isolated** | Different `series_id` → different `series_entity_id` even for same `source_name` + `entity_type` |
| **Entity Type Aware** | Same source name, different entity type → different ID (e.g., "正泰" as CHARACTER vs ORGANIZATION) |

### 5.3 Reuse vs Extend Decision

| Existing Scheme | Assessment | Decision |
|-----------------|------------|----------|
| `generate_entity_id(entity_type, source_name)` (RM-7.3) | MD5-based, no series prefix, global | **DO NOT REUSE** — lacks namespace isolation |
| `SeriesIdentity.compute_series_id()` | SHA256-based, deterministic | **REUSE PATTERN** — apply same canonicalization + SHA256 |
| `SeriesMemoryStore.compute_series_character_id()` | `schar_{sha256(series_id|korean)[:16]}` | **EXTEND PATTERN** — add `entity_type` dimension |

**Decision:** Create new `compute_series_entity_id()` following the Series Memory pattern, adding `entity_type` to the hash input. Do not modify existing `generate_entity_id()` or global `EntityIdentityRegistry`.

---

## 6. Cross-Series Isolation — Hard Failure Analysis

| Case | Current Behavior | Required Behavior | Failure Mode |
|------|------------------|-------------------|--------------|
| Same Korean entity name in Series A and B | Global registry collision | Different `series_entity_id` | **HARD FAIL** if collision detected |
| Same translated name in Series A and B | Global registry collision | Different `series_entity_id` | **HARD FAIL** if collision detected |
| Same alias in Series A and B | Global registry collision | Different `series_entity_id` | **HARD FAIL** if collision detected |
| Same canonical key in different Series | N/A (no series registry) | Different `series_entity_id` | **HARD FAIL** if collision detected |
| Entity promotion from Series A | N/A | Only affects Series A registry | **HARD FAIL** if leaks to Series B |
| Entity hydration into Book of Series B | N/A | Only Series B registry consulted | **HARD FAIL** if Series A data used |
| Registry lookup without explicit SeriesIdentity | Global registry returns wrong series | **MUST REQUIRE** explicit `series_id` | **HARD FAIL** if missing |
| Persistence path collision | N/A | `output/series/{series_id}/series_entities_{series_id}.json` | **HARD FAIL** if wrong directory |

**All cases MUST be hard failures.** No silent fallback, no auto-merge.

---

## 7. Entity Lifecycle — State Machine Analysis

**Decision: YES — SeriesEntityRegistry requires a minimal lifecycle/state machine.**

### 7.1 States

| State | Description | Trigger |
|-------|-------------|---------|
| **CREATED** | New SeriesEntityRecord added to registry | `registry.register()` or promotion |
| **ACTIVE** | Canonical mapping in use, available for hydration | Default after CREATED |
| **SUPERSEDED** | Newer version exists (version increment) | `registry.update_target()` with new value |
| **ARCHIVED** | Series archived, registry read-only | `SeriesRegistry.archive(series_id)` cascades |

### 7.2 Legal Transitions

```
CREATED → ACTIVE (automatic)
ACTIVE → SUPERSEDED (user updates canonical target)
SUPERSEDED → ACTIVE (new version becomes current)
* → ARCHIVED (series archived, terminal)
```

### 7.3 Field Mutability

| Field | Mutability | Notes |
|-------|------------|-------|
| `series_entity_id` | **IMMUTABLE** | Generated at creation |
| `source_name` | **IMMUTABLE** | Korean source never changes |
| `canonical_target` | **MUTABLE** (via SUPERSEDED) | Version increments, audit trail |
| `entity_type` | **IMMUTABLE** | Type fixed at creation |
| `source_level` | **IMMUTABLE** | Always USER for series registry |
| `metadata` | **MUTABLE** (append-only) | Add provenance, book_coverage |
| `approved_at` | **IMMUTABLE** (per version) | Timestamp of each version |
| `approved_by` | **MUTABLE** (per version) | "user" or "series_promotion" |
| `version` | **AUTO-INCREMENT** | Starts at 1, increments on update |

### 7.4 Archive Behavior

- On `SeriesRegistry.archive(series_id)`: SeriesEntityRegistry becomes read-only
- No new registrations, updates, or promotions allowed
- Existing records remain queryable for hydration

### 7.5 Deletion Behavior

**NO DELETION.** Series entities are permanent canonical records.
- Use `SUPERSEDED` for corrections
- Archive at series level for end-of-life

### 7.6 Conflict Behavior

| Scenario | Behavior |
|----------|----------|
| Register same `series_entity_id` with different `canonical_target` | **CONFLICT** — raise exception, require MANUAL resolution |
| Register same `source_name` + `entity_type` but different `series_id` | **ALLOWED** — different `series_entity_id` (namespace isolation) |
| Promote from book with conflicting target | **CONFLICT** — `AddResult.disposition = "conflict"`, audit trail |

---

## 8. Manifest Integration

### 8.1 SeriesManifest Authority Boundary (Per D-03)

| Manifest Field | Authority | SeriesEntityRegistry Relationship |
|----------------|-----------|-----------------------------------|
| `series_id` | Manifest (IMMUTABLE) | Registry keyed by this |
| `series_name` | Manifest (MUTABLE) | Registry references for display |
| `books[]` | Manifest (APPEND-ONLY) | Registry tracks `source_books` per entity |
| `series_memory_hash` | Derived (SeriesMemoryStore) | Independent |
| `series_checkpoint_hash` | Derived (SeriesCheckpoint) | Independent |
| **NEW: `series_entity_registry_hash`** | **Derived (SeriesEntityRegistry)** | **ADD to manifest** |

### 8.2 Required Manifest Extension

Add to `SeriesManifest` (Batch 5.3 scope):
```python
series_entity_registry_hash: str = ""  # DERIVED — SHA256 of SeriesEntityRegistry payload
```

**Default empty string** for backward compatibility with pre-Batch 5.3 manifests.

**Rationale:** Manifest is single source of truth. Derived hashes allow integrity verification without duplicating authority.

### 8.3 Derived-State Boundary (Explicit Contract)

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

### 8.4 No Overwrite Rule

SeriesEntityRegistry **must never** overwrite Manifest fields.
- `series_id` comes from Manifest
- `series_name` for display comes from Manifest
- Registry only stores derived `series_entity_registry_hash` back to Manifest

### 8.5 Schema Version Handling

| Aspect | Decision |
|--------|----------|
| `schema_version` | **UNCHANGED** — remains `"1.0"`. Adding a derived field with default empty string is backward-compatible, not a schema break. |
| `schema_name` | **UNCHANGED** — remains `"ntpe.series_manifest"` |

**Rationale:** The `series_memory_hash` and `series_checkpoint_hash` fields were added in Batch 5.1/5.2 with the same `"1.0"` schema version. This follows the established pattern: derived fields use default empty string in `from_dict`, making old manifests loadable without version bump.

### 8.6 Canonical Serialization & Manifest Fingerprint

- **Canonical dict includes the new field** — `to_canonical_dict()` returns all fields except `manifest_fingerprint`, including `series_entity_registry_hash`
- **Fingerprint changes when registry hash changes** — This is EXPECTED behavior for derived fields (same as `series_memory_hash` and `series_checkpoint_hash`)
- **Deterministic** — Same registry state → same manifest fingerprint

### 8.7 Backward Compatibility / Fail-Closed Behavior

| Scenario | Behavior |
|----------|----------|
| Load pre-Batch 5.3 manifest (no `series_entity_registry_hash` field) | `from_dict` uses `.get("series_entity_registry_hash", "")` → empty string. Load succeeds. |
| Load manifest with empty `series_entity_registry_hash` | Treated as "registry not yet initialized" — valid state. |
| Registry hash computed but manifest not yet updated | Manifest fingerprint will mismatch on next load → `IntegrityError` (fail-closed). Caller must call `update_series_entity_registry_hash()` after registry changes. |
| Corrupted manifest (fingerprint mismatch) | `IntegrityError` — fail-closed, no partial load. |

**Fail-Closed Principle:** Any fingerprint mismatch → exception. No silent fallback.

### 8.8 Batch 5.3 Modification Scope

**Batch 5.3 IS PERMITTED to modify `SeriesManifest`** for this derived field addition because:
1. Follows established pattern from Batch 5.1/5.2 (`series_memory_hash`, `series_checkpoint_hash`)
2. Additive only — new field with default empty string
3. No schema version bump required
4. Backward compatible via `.get()` with default
5. No authority boundary violation — field is derived, read-only from registry perspective

**No additive compatibility mechanism needed** — the existing `from_dict` pattern with `.get(field, "")` handles it.

---

## 9. Persistence Design

### 9.1 Artifact Location

```
output/
└── series/
    └── {series_id}/
        ├── series_manifest_{series_id}.json       (Batch 5.1)
        ├── series_memory_{series_id}.json         (Batch 5.2)
        ├── series_entities_{series_id}.json       (Batch 5.3 — NEW)
        ├── series_glossary_{series_id}.json       (Batch 5.4)
        ├── series_knowledge_{series_id}.json      (Batch 5.5)
        └── series_checkpoint_{series_id}.json     (Batch 5.6)
```

### 9.2 File Naming

| File | Template | Example |
|------|----------|---------|
| Entity Registry | `series_entities_{series_id}.json` | `series_entities_a1b2c3d4e5f6g7h8.json` |

### 9.3 Canonical Serialization

```python
def to_canonical_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def compute_series_entity_registry_fingerprint(payload: dict) -> str:
    # Exclude fingerprint field itself
    canonical = to_canonical_json({k: v for k, v in payload.items() if k != "series_entity_registry_fingerprint"})
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 9.4 Payload Structure

```json
{
  "schema_name": "ntpe.series_entity_registry",
  "schema_version": "1.0",
  "series_id": "a1b2c3d4e5f6g7h8",
  "entities": [
    {
      "series_entity_id": "sentity_a1b2c3d4e5f6g7h8",
      "source_name": "정태의",
      "canonical_target": "鄭泰義",
      "entity_type": "CHARACTER",
      "source_level": "USER",
      "metadata": {
        "source_books": ["book_id_1", "book_id_2"],
        "book_coverage": 2
      },
      "approved_at": "2026-08-18T00:00:00Z",
      "approved_by": "user",
      "version": 1
    }
  ],
  "series_entity_registry_fingerprint": "sha256..."
}
```

### 9.5 Corruption Handling — Fail-Closed

| Scenario | Behavior |
|----------|----------|
| File not found | Return empty registry (not error — fresh series) |
| Invalid JSON | `SeriesEntityValidationError` — operation aborted |
| Schema mismatch | `SeriesEntityValidationError` — operation aborted |
| Fingerprint mismatch | `SeriesEntityIntegrityError` — operation aborted |
| Duplicate `series_entity_id` with different data | `SeriesEntityValidationError` — operation aborted |
| ID doesn't match computed `series_entity_id` | `SeriesEntityValidationError` — operation aborted |

### 9.6 Restart Continuity

- Load registry from disk on `SeriesEntityRegistry` instantiation
- Verify fingerprint → if valid, registry ready for hydration
- If invalid → fail-closed, require manual recovery

### 9.7 Atomicity

- Write to temp file → atomic rename (`os.replace`)
- Fingerprint computed before write
- No partial writes visible

### 9.8 Cross-Series Collision Prevention

- File path includes `series_id` directory → physical isolation
- `series_entity_id` includes `series_id` prefix → logical isolation
- Load validates `series_id` in payload matches directory name

---

## 10. Hydration Design (Series → Book)

### 10.1 Hydration Trigger Points

1. **EntityResolver Initialization** — When book translation starts with `series_id`
2. **Explicit API Call** — `SeriesEntityRegistry.hydrate_resolver(resolver, book_identity)`

### 10.2 Hydration Data Flow

```
SeriesEntityRegistry (persistent USER overrides)
    │
    ├── For each SeriesEntityRecord:
    │     source_name → canonical_target
    │     entity_type preserved
    │
    ▼
EntityResolver.user_overrides[source_name] = canonical_target
    │
    ▼
Resolution Precedence: SERIES (USER) > RUNTIME > LEARNING > AUTO
```

### 10.3 Allowed Hydration Fields

| Series Field | Hydrated As | Allowed? |
|--------------|-------------|----------|
| `source_name` | `user_overrides` key | ✅ YES |
| `canonical_target` | `user_overrides` value | ✅ YES |
| `entity_type` | Metadata for resolver | ✅ YES |
| `metadata.source_books` | Provenance tracking | ✅ YES |
| `approved_by`, `approved_at` | Audit metadata | ✅ YES |

### 10.4 Forbidden Hydration Fields

| Field | Reason |
|-------|--------|
| Scene/chapter state | Book-local transient state |
| Temporary inference | Not canonical, not approved |
| Unresolved candidates | Only APPROVED records in registry |
| PENDING/CONFLICT status | Registry only stores canonical USER-level facts |

### 10.5 Hydration Idempotency

- Hydration is **idempotent** — re-running produces same `user_overrides`
- Uses `series_entity_registry_hash` in Manifest to detect changes
- Resolver tracks `hydration_source = f"series:{series_id}:{registry_hash}"`

---

## 11. Promotion Design (Book → Series)

### 11.1 Promotion Boundary

**Series owns canonical entity mappings. Book proposes. Promotion requires MANUAL approval.**

### 11.2 Promotion Triggers

- Explicit user action: `SeriesEntityRegistry.promote_from_book(resolver, book_identity, approval_gate=True)`
- After book translation completes and user reviews entity mappings
- **NOT automatic** — D-07 frozen: MANUAL for all entity types

### 11.3 Promotion Logic

| Book State | Series State | Action |
|------------|--------------|--------|
| No existing entry | — | **CREATE** new SeriesEntityRecord |
| Same `source_name` + `entity_type`, SAME `canonical_target` | — | **NO-OP** (already canonical) |
| Same `source_name` + `entity_type`, DIFFERENT `canonical_target` | — | **CONFLICT** — requires MANUAL resolution |
| User override from book translation | Registry has entry | Compare targets, same/conflict logic |
| Learning data (confidence ≥0.8) | Registry has entry | **NOT PROMOTED** — learning is not USER level |

### 11.4 Promotion Record (Audit Trail)

```python
@dataclass(frozen=True)
class EntityPromotionRecord:
    promotion_id: str           # sha256(series_id|book_id|source|timestamp)[:12]
    series_id: str
    book_identity: str
    source_name: str
    entity_type: str
    previous_target: str | None
    new_target: str
    action: str                 # "created" | "no_op" | "conflict"
    resolved_by: str | None     # "user" | None (for conflict)
    resolved_at: str
    source_level: str           # "USER_OVERRIDE" | "LEARNING"
```

### 11.5 Promotion Policy (Frozen — D-07)

```python
@dataclass(frozen=True)
class EntityPromotionPolicy:
    auto_promote_user_overrides: bool = False   # MANUAL only
    auto_promote_learning: bool = False         # NEVER
    conflict_resolution: str = "manual"         # "manual" only
    require_user_approval: bool = True          # Always True
```

---

## 12. Acceptance Test Matrix for Batch 5.3

| Test ID | Category | Description | Expected Result | Failure Condition |
|---------|----------|-------------|-----------------|-------------------|
| **SE-01** | Deterministic Identity | Same `(series_id, source, type)` → same `series_entity_id` | Identical IDs across runs/machines | Different IDs |
| **SE-02** | Same-Series Resolution | Register entity, resolve via registry | Returns correct `canonical_target` | Wrong target or not found |
| **SE-03** | Cross-Series Isolation | Series A "정태의" vs Series B "正泰" | Different `series_entity_id`, no leakage | Same ID or cross-leak |
| **SE-04** | Alias Isolation | Series A alias "태의" vs Series B alias "태의" | Different registry entries | Cross-series alias resolution |
| **SE-05** | Persistence Isolation | Save Series A, load Series B | Independent files, no collision | Wrong file loaded |
| **SE-06** | Hydration Isolation | Hydrate Series A registry into Book B resolver | Book B resolver gets Series B entities only | Series A entities in Book B |
| **SE-07** | Promotion MANUAL Gate | Attempt promotion with `approval_gate=False` | Exception raised | Auto-promotion succeeds |
| **SE-08** | Conflict Detection | Promote different target for same source | `AddResult.disposition = "conflict"` | Silent overwrite or no conflict |
| **SE-09** | Corruption Rejection | Tamper registry file fingerprint | `SeriesEntityIntegrityError` on load | Load succeeds with corrupted data |
| **SE-10** | Restart Continuity | Save → restart process → load → hydrate | Same registry state, hydration works | Data loss or hydration fails |
| **SE-11** | Lifecycle Behavior | Create → supersede → archive | Version increments, archive read-only | Version not incremented or write after archive |
| **SE-12** | Frozen Contract Isolation | EntityResolver core logic unchanged | Existing tests PASS, precedence SERIES>RUNTIME | Core resolver modified |
| **SE-13** | Provider/Network/Translation | Run all Batch 5.3 tests | 0/0/0 execution | Any external call |
| **SE-14** | Root Hygiene | Check repo root after test run | No new files in root | Files created in root |
| **SE-15** | Entity Type Isolation | Same source, different type (CHARACTER vs PLACE) | Different `series_entity_id` | Same ID for different types |

---

## 13. Decisions Summary

| Decision | Status | Rationale |
|----------|--------|-----------|
| **Series Entity ID Format** | `sentity_{sha256(series_id|source|type)[:16]}` | Consistent with `schar_`, `sfact_` patterns; adds entity_type dimension |
| **EntityResolver Precedence** | SERIES (USER level) > RUNTIME > LEARNING > AUTO | Series registry = persistent USER override (Formal Spec §6.3) |
| **Promotion Default** | MANUAL for all entity types (D-07 frozen) | No auto-promotion; user must explicitly approve |
| **Lifecycle** | Minimal: CREATED → ACTIVE → SUPERSEDED → ARCHIVED | Canonical facts are immutable-ish; versioning for audit |
| **Manifest Hash** | Add `series_entity_registry_hash` to SeriesManifest | Single source of truth for derived state |
| **Global Registry Replacement** | Do NOT modify `core/entity_normalization/identity.py` | Batch 5.3 adds new module; RM-7.3 global registry deprecated for series use |
| **Conflict Behavior** | Hard failure on collision, MANUAL resolution required | Fail-closed, no silent data corruption |
| **Hydration Scope** | All SeriesEntityRecord → EntityResolver.user_overrides | Complete canonical projection at USER level |
| **EntityResolver Integration Boundary** | EXISTING `user_overrides` parameter only | No modifications to `core/entity_resolver/` files; uses authorized extension point from RM-7.2 |
| **SeriesManifest Derived-State Boundary** | One-way: Registry → Manifest | `series_entity_registry_hash` is DERIVED, read-only from registry; never authority; schema_version unchanged at "1.0" |

---

## 14. Owner Decisions — FROZEN (Owner Confirmed 2026-08-20)

All decisions below are **OWNER-CONFIRMED and FROZEN** for Batch 5.3 implementation.

| Decision | Options | FROZEN Choice |
|----------|---------|---------------|
| **SE-1: Entity Type Set** | Use RM-7.2 `EntityType` (CHARACTER, PLACE, ORGANIZATION, TERMINOLOGY, UNKNOWN) vs RM-7.3 `EntityType` (CHARACTER, LOCATION, ORGANIZATION, TERM) | **RM-7.2 set** — FROZEN |
| **SE-2: Name Forms in Registry** | Store full `EntityNameForms` in SeriesEntityRecord vs Store only canonical_target + metadata | **Minimal — canonical_target only** — FROZEN |
| **SE-3: Registry Query API** | `get_by_source(source_name)` only vs `get_by_source(source_name, entity_type)` | **Typed query — require entity_type** — FROZEN |
| **SE-4: EntityResolver Integration Boundary** | (a) Modify EntityResolver core to add series_registry parameter (b) Use EXISTING user_overrides extension point (c) Defer to Batch 5.7 | **Option (b) — Use EXISTING user_overrides extension point only** — FROZEN. EntityResolver core remains UNCHANGED. |
| **SE-5: SeriesEntityRecord.version** | Per-record version vs registry-level version | **Per-record version** — FROZEN |

---

## 15. Blockers
2. **Batch 5.2 must be accepted** (provides `series_id`, `SeriesManifest`, `SeriesMemoryStore` primitives)
3. **No blocker from existing code** — all changes additive, no frozen contracts modified

---

## 16. Deliverables

1. `docs/governance/rm8/P0_STAGE5_BATCH5_3_SERIES_ENTITY_PREFLIGHT_AUDIT.md` (this document)
2. `docs/governance/rm8/P0_STAGE5_BATCH5_3_IMPLEMENTATION_TASK.md` (implementation specification)

---

## 17. Validation Results (Preflight)

| Check | Result |
|-------|--------|
| `ntpe_validate.py` | PASS (baseline) |
| `python -m compileall core/` | PASS (0 errors) |
| `git diff --check` | PASS (clean) |
| Provider Execution | 0 (audit only) |
| Network Calls | 0 (audit only) |
| Translation Execution | 0 (audit only) |
| Root Hygiene | PASS (no root files created) |
| Production Code Modified | NO (audit only) |

---

## 18. Final Verdict

### Is NTPE Ready for Batch 5.3 Implementation?

> **NOT READY — OWNER DECISION REQUIRED**

### Blocking Reasons:

1. **Owner Decisions Required** on 5 architectural questions (SE-1 to SE-5)
2. **Batch 5.2 Acceptance Pending** — Series Memory Store must be baseline

### Next Steps:

1. Owner reviews and decides on SE-1 ~ SE-5
2. Upon decisions → Update implementation task with confirmed choices
3. Authorize Batch 5.3 implementation

---

*End of Preflight Audit. No production code modified. Awaiting Owner decisions on SE-1 ~ SE-5.*