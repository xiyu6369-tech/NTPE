# P0 Stage 5 Batch 5.4 — Series Glossary Implementation Task

**Baseline Commit:** `b13a6ec0df4882a060ba9cf02ed81e2803790a52` (P0 Stage 5 Batch 5.3 Accepted)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` (§7, §9, §13, §20, §24, §25)
**Amendment:** `docs/governance/rm8/P0_STAGE5_SPECIFICATION_AMENDMENT.md`
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md` (Batch 5.4)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_BATCH5_4_PREFLIGHT_AUDIT.md`
**Task Status:** Specification Complete — Ready for Owner Authorization
**Implementation Status:** NOT STARTED

---

## 1. Objective

Implement the **Series Glossary** for P0 Stage 5 Series Continuity.

**Deliverables:**
- Extensions to `core/glossary_builder.py` with three new functions:
  - `build_series_glossary()` — Build canonical glossary from completed books in series
  - `load_series_glossary()` — Load persisted SeriesGlossary from disk
  - `merge_into_series_glossary()` — Merge book glossary into SeriesGlossary (promotion)
- Deterministic persistence: `series_glossary_{series_id}.json` with SHA-256 integrity
- SeriesManifest integration via `series_glossary_hash` derived field
- Hydration into Book glossary and GlossaryContext (read-only projection)
- MANUAL promotion gate (D-07 frozen)
- Cross-series isolation via `series_id` namespace
- CSI-03 hard gate for glossary isolation

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **SeriesGlossaryTerm Model** | Canonical glossary term: `source`, `translation`, `category`, `locked`, `status`, `source_books`, `book_coverage`, `confidence`, `aliases`, `notes`, `approved_at`, `approved_by`, `version` |
| **SeriesGlossary Model** | Container with `schema_name`, `schema_version`, `series_id`, `terms` dict, `glossary_hash` |
| **Glossary Builder Extensions** | `build_series_glossary(series_id, series_manifest)`, `load_series_glossary(series_id, output_root)`, `merge_into_series_glossary(series_glossary, book_glossary, book_identity, approval_gate)` |
| **Persistence** | Deterministic JSON serialization (`series_glossary_{series_id}.json`) with canonical JSON + SHA-256 fingerprint |
| **Hydration (Series → Book)** | SeriesGlossary locked terms → Book glossary / GlossaryContext as locked terms |
| **Promotion (Book → Series)** | MANUAL approval-gated promotion of locked/high-confidence terms from completed books |
| **Validation & Conflict Detection** | Schema validation, fingerprint verification, conflict detection on differing translations |
| **Manifest Integration** | Add `series_glossary_hash` to `SeriesManifest` (derived field, additive) |
| **Cross-Series Isolation** | Enforce `series_id` namespace in file paths, manifest, and all operations |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| New `core/series_glossary/` module | Batch Plan: No new module — extend `glossary_builder.py` |
| Modify `core/glossary.py` | **FROZEN** (Glossary class, prompt_block, apply_output_fix) |
| Modify `core/translation_resources/glossary_resource.py` | **FROZEN** |
| Modify `core/literary/glossary_context.py` | **FROZEN** (GlossaryContext, LockedTerm) |
| Series Knowledge Population | Batch 5.5 |
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
core/glossary_builder.py (EXTENDED)
    ├── [EXISTING] merge_glossary(), apply_override(), finalize_glossary()
    ├── [EXISTING] build_character_alias_index(), build_summary()
    ├── [EXISTING] save_glossary(), save_report(), save_csv()
    ├── [NEW] build_series_glossary(series_id, series_manifest, output_root)
    ├── [NEW] load_series_glossary(series_id, output_root)
    ├── [NEW] merge_into_series_glossary(series_glossary, book_glossary, book_identity, approval_gate)
    ├── [NEW] SeriesGlossaryTerm dataclass
    ├── [NEW] SeriesGlossary dataclass
    ├── [NEW] compute_series_glossary_fingerprint()
    ├── [NEW] save_series_glossary(), load_series_glossary_from_path()
    ├── [NEW] validate_series_glossary()
    └── [NEW] SeriesGlossaryValidationError, SeriesGlossaryIntegrityError
```

### 4.2 Dependency / Ownership Diagram

```
SeriesGlossary (Series-Level Owner)
    ├── persistence (series_glossary_{series_id}.json)
    ├── validation (schema, fingerprint, cross-series)
    ├── promotion (Book → Series, MANUAL gate)
    ├── hydration (Series → Book, read-only projection)
    ├── cross-volume merge (completed books only)
    ├── canonical serialization + fingerprint
    └── namespace isolation (series_id in path)
    │
    ├── GlossaryBuilder (Lower-Level Consumer)
    │   ├── Reads SeriesManifest for completed books
    │   ├── Produces book glossaries (analysis files)
    │   └── No dependency on SeriesGlossary internals
    │
    ├── Frozen Components (Adapters Only)
    │   ├── core/glossary.py → adapter loads SeriesGlossary terms
    │   ├── core/literary/glossary_context.py → adapter passes locked_dictionary
    │   └── core/translation_resources/glossary_resource.py → unchanged
    │
    └── SeriesManifest (Authority for derived hash)
        └── series_glossary_hash (DERIVED, read-only from glossary perspective)
```

**Forbidden:** Bidirectional dependency `GlossaryBuilder ↔ SeriesGlossary`

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.series_identity` | Internal | `SeriesIdentity`, `SeriesManifest`, `SeriesRegistry`, `BookStatus`, `get_series_dir()` |
| `core.glossary_builder` (self) | Internal | Existing merge, classification, confidence logic (read-only) |

**No dependencies on:** `core.character_memory_v2`, `core.context_scene_memory`, `core.entity_resolver`, `core.knowledge_runtime`, `core.book_intake`, `core.translation_runtime`, `core.runtime_checkpoint`

---

## 5. Data Models

### 5.1 SeriesGlossaryTerm

```python
@dataclass(frozen=True)
class SeriesGlossaryTerm:
    """Persistent canonical glossary term — series-scoped."""
    source: str                          # Korean source term
    translation: str                     # Approved Chinese translation
    category: str                        # From classify_term(): person_name, abbreviation, code, english_term, unknown
    locked: bool                         # True if manually locked OR confidence >= 0.95
    status: str                          # "manual_locked" | "auto_high_confidence" | "series_canonical"
    source_books: tuple[str, ...]        # Book identities where term appears (completed books only)
    book_coverage: int                   # Number of completed books containing term
    confidence: float                    # Aggregated confidence (1.0 if locked)
    aliases: tuple[str, ...]             # Known aliases/variants
    notes: tuple[str, ...]               # Provenance notes
    approved_at: str                     # ISO timestamp of this version
    approved_by: str                     # "user" | "series_promotion" | "auto_high_confidence"
    version: int                         # Starts at 1, increments on update
```

### 5.2 SeriesGlossary

```python
@dataclass(frozen=True)
class SeriesGlossary:
    """Series-canonical glossary — persistent across volumes."""
    schema_name: str                         # "ntpe.series_glossary"
    schema_version: str                      # "1.0"
    series_id: str                           # From SeriesManifest
    terms: dict[str, SeriesGlossaryTerm]     # Keyed by source term
    glossary_hash: str                       # SHA-256 of canonical payload (excluding hash itself)
```

### 5.3 GlossaryPromotionRecord (Audit Trail)

```python
@dataclass(frozen=True)
class GlossaryPromotionRecord:
    """Audit trail for Book → Series glossary promotion."""
    promotion_id: str           # sha256(series_id|book_id|source|timestamp)[:12]
    series_id: str
    book_identity: str
    source_term: str
    previous_translation: str | None
    new_translation: str
    action: str                 # "created" | "no_op" | "conflict" | "updated"
    resolved_by: str | None     # "user" | None (for conflict)
    resolved_at: str
    source_status: str          # "locked" | "auto_high_confidence"
```

---

## 6. Series Glossary Identity Semantics

### 6.1 Namespace Isolation

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_glossary_{series_id}.json` |
| **Manifest Key** | All operations require explicit `series_id` |
| **Hydration** | Only glossary matching `series_id` consulted |
| **Promotion** | Only book glossary from matching `series_id` series promoted |
| **Load Validation** | Payload `series_id` must match directory name |

### 6.2 Term Key

Terms are keyed by `source` string directly. No per-term UUID needed — isolation via `series_id` directory and manifest.

---

## 7. Serialization Rules

### 7.1 Canonical JSON

```python
def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 7.2 Series Glossary Fingerprint

```python
def compute_series_glossary_fingerprint(series_glossary_dict: dict) -> str:
    """Compute SHA-256 of canonical glossary payload (excluding glossary_hash itself)."""
    payload = {k: v for k, v in series_glossary_dict.items() if k != "glossary_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 7.3 Round-Trip Guarantee

```
series_glossary → to_canonical_json → bytes → sha256 → glossary_hash
series_glossary → to_dict() → load → serialize → same glossary_hash
```

**Deterministic:** Same inputs → bit-for-bit identical JSON → identical fingerprint.

---

## 8. Validation Rules

### 8.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_glossary" | `SeriesGlossaryValidationError` |
| `schema_version` == "1.0" | `SeriesGlossaryValidationError` |
| `series_id` matches directory/filename | `SeriesGlossaryValidationError` |
| `glossary_hash` matches computed | `SeriesGlossaryIntegrityError` (fail-closed) |
| All required fields present per term | `SeriesGlossaryValidationError` |
| `locked` == True OR `confidence` >= 0.95 for all terms | `SeriesGlossaryValidationError` |
| `confidence` in [0.0, 1.0] | `SeriesGlossaryValidationError` |
| `version` >= 1 | `SeriesGlossaryValidationError` |
| `approved_at` valid ISO 8601 UTC | `SeriesGlossaryValidationError` |
| No duplicate source terms | `SeriesGlossaryValidationError` |

### 8.2 Business Rule Validation (on Mutations)

| Operation | Validation |
|-----------|------------|
| `merge_into_series_glossary()` | Only locked or confidence>=0.95 terms; MANUAL gate enforced; book must be completed |
| `build_series_glossary()` | Only books with status="completed" or "promoted" in SeriesManifest |
| `load_series_glossary()` | Fingerprint must match; series_id must match |

### 8.3 Fail-Closed Principle

- **Any validation failure → Exception**, no partial load, no fallback defaults
- Corrupted glossary file → `SeriesGlossaryIntegrityError` → operation blocked
- No silent data corruption

---

## 9. build_series_glossary() — Cross-Volume Canonical Merge

### 9.1 Trigger

- Called when SeriesGlossary needs to be built/refreshed (e.g., after book promotion)
- Explicit API call during Series orchestration

### 9.2 Source Data

```python
def build_series_glossary(
    series_id: str,
    series_manifest: SeriesManifest,
    output_root: Path,
    character_memory_store: SeriesMemoryStore | None = None,
    entity_registry: SeriesEntityRegistry | None = None,
) -> SeriesGlossary:
    """
    Build canonical glossary from all completed books in series.

    Rules:
    - Only terms from books with status="completed" or "promoted"
    - Only terms with locked=True or confidence >= 0.95
    - Merged across all volumes (reuse existing merge_glossary logic)
    - EntityRegistry canonical names included as locked terms
    - CharacterMemory canonical names included as locked terms
    """
```

### 9.3 Build Process

1. **Collect completed book identities** from SeriesManifest
2. **Load each book's glossary** from analysis files or book glossary artifact
3. **Merge using existing `merge_glossary()`** — aggregates counts, book_coverage
4. **Apply locked/high-confidence filter** — only locked=True or confidence>=0.95
5. **Enrich with EntityRegistry** — canonical entity names as locked terms (category="person_name")
6. **Enrich with CharacterMemory** — canonical character names as locked terms
7. **Compute fingerprint** and persist

### 9.4 Term Status Assignment

| Source | SeriesGlossaryTerm.status |
|--------|---------------------------|
| Manual override (locked=True) | "manual_locked" |
| Confidence >= 0.95 (auto) | "auto_high_confidence" |
| From EntityRegistry | "series_canonical" |
| From CharacterMemory | "series_canonical" |

---

## 10. load_series_glossary() — Persistence Load

```python
def load_series_glossary(series_id: str, output_root: Path) -> SeriesGlossary:
    """
    Load SeriesGlossary from disk with integrity verification.

    Returns empty SeriesGlossary if file not found (fresh series).
    Raises SeriesGlossaryIntegrityError on fingerprint mismatch.
    Raises SeriesGlossaryValidationError on schema mismatch.
    """
```

---

## 11. merge_into_series_glossary() — Promotion (Book → Series)

### 11.1 Promotion Boundary (CRITICAL)

**Series owns canonical glossary terms. Book proposes. Promotion requires MANUAL approval.**

### 11.2 Promotion Logic

```python
def merge_into_series_glossary(
    series_glossary: SeriesGlossary,
    book_glossary: dict,           # Output from glossary_builder (terms dict)
    book_identity: str,
    approval_gate: bool = True,
) -> tuple[SeriesGlossary, tuple[GlossaryPromotionRecord, ...]]:
    """
    Promote locked/high-confidence terms from completed book to SeriesGlossary.

    Requires MANUAL approval gate (D-07 frozen).
    Only processes terms with locked=True or confidence >= 0.95.
    """
    if not approval_gate:
        raise SeriesGlossaryValidationError(
            "Glossary promotion requires MANUAL approval gate (D-07 frozen). "
            "Auto-promotion is not permitted."
        )

    # Validate book is completed in SeriesManifest
    # Process each eligible term
    # Detect conflicts: different translation for same source
    # Return updated SeriesGlossary and promotion records
```

### 11.3 Promotion Decision Matrix

| Book Term State | Series Term State | Action |
|-----------------|-------------------|--------|
| locked=True, translation=T1 | No entry | CREATE (status="manual_locked") |
| locked=True, translation=T1 | Same T1 | NO-OP |
| locked=True, translation=T1 | Different T2 | CONFLICT |
| locked=False, conf>=0.95, T1 | No entry | CREATE (status="auto_high_confidence") |
| locked=False, conf>=0.95, T1 | Same T1 | NO-OP |
| locked=False, conf>=0.95, T1 | Different T2 | CONFLICT |
| locked=False, conf<0.95 | Any | SKIP (not eligible) |

### 11.4 Promotion Policy (Fixed — Not Configurable)

```python
@dataclass(frozen=True)
class GlossaryPromotionPolicy:
    auto_promote_locked: bool = False           # MANUAL only (D-07)
    auto_promote_high_confidence: bool = False  # MANUAL only
    conflict_resolution: str = "manual"         # "manual" only
    require_user_approval: bool = True          # Always True
```

**No auto-promotion.** All promotions require explicit user action. Policy is frozen.

---

## 12. Hydration Design (Series → Book)

### 12.1 Hydration Trigger Points

1. **Book Glossary Initialization** — When book translation starts with `series_id`
2. **Explicit API Call** — `SeriesGlossary.get_locked_dictionary()`

### 12.2 Hydration Data Flow

```
SeriesGlossary (all locked terms)
    │
    ├── Filter: locked=True OR confidence >= 0.95
    │
    ▼
Locked Dictionary: {source: translation}
    │
    ├── → core/glossary.py: Glossary.terms.update(locked_dict)
    ├── → core/literary/glossary_context.py: GlossaryContext.from_locked_dictionary(locked_dict, chunk_text)
    └── → Book glossary artifact: merged with book-local terms
```

### 12.3 Adapter for Frozen Components

```python
def get_locked_dictionary(series_glossary: SeriesGlossary) -> dict[str, str]:
    """Extract locked terms for frozen component integration."""
    return {
        term.source: term.translation
        for term in series_glossary.terms.values()
        if term.locked or term.confidence >= 0.95
    }

def get_alias_map(series_glossary: SeriesGlossary) -> dict[str, str]:
    """Extract aliases for GlossaryContext alias_map."""
    alias_map = {}
    for term in series_glossary.terms.values():
        for alias in term.aliases:
            if alias not in alias_map:
                alias_map[alias] = term.translation
    return alias_map
```

### 12.4 Hydration Idempotency

- Hydration is **idempotent** — re-running produces same locked dictionary
- Uses `series_glossary_hash` in SeriesManifest to detect changes
- Book glossary tracks `hydration_source = f"series:{series_id}:{glossary_hash}"`

---

## 13. Manifest Integration

### 13.1 SeriesManifest Extension

Add to `SeriesManifest` (in `core/series_identity/manifest.py` — additive, following existing `series_memory_hash`/`series_checkpoint_hash`/`series_entity_registry_hash` pattern):

```python
@dataclass(frozen=True)
class SeriesManifest:
    # ... existing fields ...
    series_glossary_hash: str = ""  # DERIVED — SHA256 of SeriesGlossary
```

**Add supporting method:**
```python
def with_series_glossary_hash(self, hash_value: str) -> "SeriesManifest":
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
        series_glossary_hash=hash_value,
        manifest_fingerprint="",
    )
```

**Update `from_dict` for backward compatibility:**
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
        series_entity_registry_hash=data.get("series_entity_registry_hash", ""),
        series_glossary_hash=data.get("series_glossary_hash", ""),  # Default empty for old manifests
        manifest_fingerprint=data.get("manifest_fingerprint", ""),
    )
```

### 13.2 Glossary Hash Update (SeriesRegistry method)

```python
def update_series_glossary_hash(self, series_id: str, glossary_hash: str) -> SeriesManifest:
    """Update series_glossary_hash after glossary changes."""
    manifest = self.get(series_id)
    updated_manifest = manifest.with_series_glossary_hash(glossary_hash)
    fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
    updated_manifest = updated_manifest.with_fingerprint(fingerprint)
    series_dir = get_series_dir(self.output_root, series_id)
    manifest_path = manifest_file_path(series_dir, series_id)
    save_manifest(updated_manifest, manifest_path)
    return updated_manifest
```

### 13.3 Derived-State Boundary (Explicit Contract)

| Property | Requirement |
|----------|-------------|
| **Derived** | `series_glossary_hash` is computed FROM SeriesGlossary, never the reverse |
| **Read-Only from Glossary** | Glossary computes hash; Manifest stores it. Glossary never reads this field for authority. |
| **Never Authority Source** | Manifest field is a fingerprint only. Does not control glossary content. |
| **Never Overwrites SeriesIdentity** | `series_id`, `series_name`, `created_at` remain Manifest authority. |
| **Never Overwrites Canonical Terms** | Glossary owns `SeriesGlossaryTerm` content. Manifest hash is a checksum only. |

**Data Flow (ONE DIRECTION ONLY):**
```
SeriesGlossary
    → compute SHA-256 fingerprint (canonical serialization)
    → SeriesGlossary.get_glossary_hash()
    → SeriesRegistry.update_series_glossary_hash(series_id, hash)
    → SeriesManifest.series_glossary_hash (derived field)
```

### 13.4 Schema Version Handling

| Aspect | Decision |
|--------|----------|
| `schema_version` | **UNCHANGED** — remains `"1.0"`. Adding a derived field with default empty string is backward-compatible, not a schema break. |
| `schema_name` | **UNCHANGED** — remains `"ntpe.series_manifest"` |

### 13.5 Canonical Serialization & Manifest Fingerprint

- **Canonical dict includes the new field** — `to_canonical_dict()` returns all fields except `manifest_fingerprint`, including `series_glossary_hash`
- **Fingerprint changes when glossary hash changes** — EXPECTED behavior for derived fields
- **Deterministic** — Same glossary state → same manifest fingerprint

### 13.6 Backward Compatibility / Fail-Closed Behavior

| Scenario | Behavior |
|----------|----------|
| Load pre-Batch 5.4 manifest (no `series_glossary_hash` field) | `from_dict` uses `.get("series_glossary_hash", "")` → empty string. Load succeeds. |
| Load manifest with empty `series_glossary_hash` | Treated as "glossary not yet initialized" — valid state. |
| Glossary hash computed but manifest not yet updated | Manifest fingerprint will mismatch on next load → `IntegrityError` (fail-closed). Caller must call `update_series_glossary_hash()` after glossary changes. |
| Corrupted manifest (fingerprint mismatch) | `IntegrityError` — fail-closed, no partial load. |

### 13.7 Batch 5.4 Modification Scope

**Batch 5.4 IS PERMITTED to modify `SeriesManifest`** for this derived field addition because:
1. Follows established pattern from Batch 5.1/5.2/5.3 (`series_memory_hash`, `series_checkpoint_hash`, `series_entity_registry_hash`)
2. Additive only — new field with default empty string
3. No schema version bump required
4. Backward compatible via `.get()` with default
5. No authority boundary violation — field is derived, read-only from glossary perspective

---

## 14. Cross-Series Isolation (Hard Enforcement)

### 14.1 Namespace Isolation Rules

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_glossary_{series_id}.json` |
| **Manifest Key** | All queries require explicit `series_id` |
| **Hydration** | Only glossary matching `series_id` consulted |
| **Promotion** | Only book glossary from matching `series_id` series promoted |
| **Load Validation** | Payload `series_id` must match directory name |

### 14.2 Hard Failure Cases (All MUST Fail)

| Case | Validation Point |
|------|------------------|
| Load glossary with mismatched `series_id` | `load_series_glossary()` |
| Build glossary for wrong series | `build_series_glossary()` |
| Hydrate glossary into wrong series book | `get_locked_dictionary()` + book series_id check |
| Promote from book of different series | `merge_into_series_glossary()` |
| File path collision | Impossible — directory隔离 |

---

## 15. CSI-03 Acceptance Tests (Hard Gates)

> **All MUST PASS. Any failure → Batch 5.4 not accepted.**

| Test ID | Description | Verification |
|---------|-------------|--------------|
| **CSI-03** | Series A glossary locked term ≠ Series B | Verify file naming `series_glossary_{series_id}.json` and manifest hash isolation |
| **SG-01** | Deterministic build: same inputs → same glossary_hash | 1000 iterations property test |
| **SG-02** | Cross-series isolation: Series A "正泰的" vs Series B "正泰的" | Different files, no leakage |
| **SG-03** | Completed-books-only: `in_progress` books excluded | Terms from in_progress not in glossary |
| **SG-04** | Locked term precedence: Series locked overrides book auto | Book term not used if series has locked |
| **SG-05** | Confidence threshold: ≥0.95 promoted, <0.95 not | Low-confidence not in glossary |
| **SG-06** | Persistence integrity: save → load → hash matches | Hash matches |
| **SG-07** | Corruption rejection: tampered fingerprint → IntegrityError | Fail-closed on load |
| **SG-08** | Hydration isolation: Series A glossary → Book B resolver | Book B gets Series B terms only |
| **SG-09** | Promotion MANUAL gate: `approval_gate=False` raises | Exception on auto-promote |
| **SG-10** | Conflict detection: different translation → CONFLICT | Conflict recorded, no silent overwrite |
| **SG-11** | Manifest hash integration: glossary hash in SeriesManifest | Hash present, updates on glossary change |
| **SG-12** | Backward compat: old manifest loads | Empty string default |
| **SG-13** | Provider/Network/Translation = 0/0/0 | Verified in test runs |
| **SG-14** | Root hygiene: no files in repo root | Git status clean |
| **SG-15** | Frozen contract isolation: glossary.py, glossary_context.py unchanged | Existing tests PASS |

---

## 16. Frozen Contracts Audit

**Batch 5.4 MUST NOT modify (to be verified):**

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
| Entity Resolver core | No touch |
| KnowledgeRuntime core | No touch |
| Runtime Checkpoint core | No touch |
| **core/glossary.py** | **FROZEN** — No modifications |
| **core/literary/glossary_context.py** | **FROZEN** — No modifications |
| **core/translation_resources/glossary_resource.py** | **FROZEN** — No modifications |

**New Contract Created by Batch 5.4:**
- **Series Glossary Contract** (extensions to `core/glossary_builder.py`) — to be added to Foundation Manifest in Batch 5.9

---

## 17. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/glossary.py` | **FROZEN** |
| `core/literary/glossary_context.py` | **FROZEN** |
| `core/translation_resources/glossary_resource.py` | **FROZEN** |
| `core/character_memory_v2/` | **FROZEN** |
| `core/context_scene_memory/` | **FROZEN** |
| `core/entity_resolver/` | **FROZEN** |
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

---

## 18. Test Requirements

### 18.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_series_glossary_term_creation` | Create term with all fields |
| `test_series_glossary_term_immutability` | Frozen dataclass enforcement |
| `test_series_glossary_creation` | Build glossary with terms |
| `test_series_glossary_serialization_roundtrip` | Save → load → fingerprint matches |
| `test_series_glossary_fingerprint_integrity` | Tampered file → IntegrityError |
| `test_build_series_glossary_completed_only` | Only completed/promoted books contribute |
| `test_build_series_glossary_locked_high_conf` | Only locked or confidence>=0.95 included |
| `test_merge_into_series_glossary_new_term` | New locked term → CREATED |
| `test_merge_into_series_glossary_same_translation` | Same translation → NO-OP |
| `test_merge_into_series_glossary_conflict` | Different translation → CONFLICT |
| `test_merge_into_series_glossary_manual_gate` | `approval_gate=False` → exception |
| `test_hydration_locked_dictionary` | Extract locked terms for frozen components |
| `test_hydration_idempotent` | Multiple hydrations → same dictionary |
| `test_namespace_isolation` | Series A terms not in Series B glossary |
| `test_persistence_roundtrip` | Save → load → fingerprint matches |
| `test_persistence_corrupted_fail_closed` | Corrupted file → IntegrityError |
| `test_deterministic_serialization` | Same glossary → bit-for-bit identical JSON |
| `test_manifest_hash_integration` | Glossary hash stored in SeriesManifest |
| `test_manifest_hash_updates` | Manifest fingerprint changes with glossary |
| `test_old_manifest_loads` | Pre-Batch 5.4 manifest loads with empty hash |

### 18.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_glossary_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |
| `test_hydration_idempotent_property` | 1000 |
| `test_build_glossary_deterministic` | 1000 |

### 18.3 Cross-Series Isolation Tests (CSI-03)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_03_glossary_file_isolation` | CSI-03 |

### 18.4 Integration Tests

| Test | Description |
|------|-------------|
| `test_series_glossary_in_book2_translation` | Book 1 promote → Book 2 hydrate → locked terms present |
| `test_cross_series_no_leakage_glossary` | Series A glossary not in Series B book |
| `test_frozen_glossary_integration` | `core/glossary.py` loads SeriesGlossary terms correctly |
| `test_glossary_context_integration` | `GlossaryContext.from_locked_dictionary()` works with SeriesGlossary |

---

## 19. Batch 5.4 Acceptance Test Matrix (Comprehensive)

| Category | Test | Description | Pass Criteria |
|----------|------|-------------|---------------|
| **Persistence** | `test_persist_save_load` | Save glossary, load, verify fingerprint | Fingerprint matches, terms intact |
| **Persistence** | `test_persist_corrupted_fail_closed` | Corrupt JSON, attempt load | `SeriesGlossaryIntegrityError` raised |
| **Persistence** | `test_persist_missing_file` | Load non-existent glossary | Empty SeriesGlossary |
| **Persistence** | `test_persist_restart` | Process restart simulation | Reload produces identical state |
| **Reload** | `test_reload_idempotent` | Load → save → load → save | Bit-for-bit identical JSON |
| **Promotion** | `test_promote_locked_term` | Promote locked term from Book 1 | SeriesGlossaryTerm created |
| **Promotion** | `test_promote_high_confidence` | Promote confidence>=0.95 term | SeriesGlossaryTerm created |
| **Promotion** | `test_promote_same_translation` | Promote same translation as series | NO-OP, no duplicate |
| **Promotion** | `test_promote_conflict` | Promote different translation | CONFLICT, requires MANUAL |
| **Promotion** | `test_promote_low_confidence_blocked` | Attempt promote confidence<0.95 | Blocked, not promoted |
| **Approval Gate** | `test_approval_manual_only` | Verify no auto-promotion path exists | All promotions require user action |
| **Approval Gate** | `test_approval_audit_trail` | Verify GlossaryPromotionRecord created | Complete audit trail per promotion |
| **Conflict Handling** | `test_conflict_detection` | Different translation for same source | Conflict detected, no silent overwrite |
| **Conflict Handling** | `test_conflict_resolution_manual` | User resolves conflict, series updated | Series updated, audit trail recorded |
| **Hydration** | `test_hydrate_locked_terms` | Series locked terms → locked_dictionary | All locked terms extracted |
| **Hydration** | `test_hydrate_idempotent` | Hydrate twice | Identical locked_dictionary |
| **Hydration** | `test_hydrate_frozen_glossary` | SeriesGlossary → core/glossary.py | Glossary.terms updated |
| **Hydration** | `test_hydrate_glossary_context` | SeriesGlossary → GlossaryContext | LockedTerm list populated |
| **Cross-Series Isolation** | `test_isolation_same_source` | Series A "正泰的" vs Series B "正泰的" | Different files, no leakage |
| **Cross-Series Isolation** | `test_isolation_promotion_gated` | Promote in Series A, verify Series B clean | Series B unaffected |
| **Cross-Series Isolation** | `test_isolation_filesystem` | Delete Series A dir, Series B intact | No cross-directory references |
| **Corruption** | `test_corruption_fingerprint` | Tamper fingerprint | IntegrityError on load |
| **Corruption** | `test_corruption_json` | Malformed JSON | ValidationError on load |
| **Corruption** | `test_corruption_schema` | Wrong schema_name/version | ValidationError on load |
| **Deterministic Serialization** | `test_deterministic_json` | Same terms, multiple serializations | Bit-for-bit identical |
| **Deterministic Serialization** | `test_deterministic_hash` | Same terms, multiple hashes | Identical SHA-256 |
| **Process Restart** | `test_restart_continuity` | Simulate restart, reload glossary | Locked terms available for Book 2 |
| **Backward Compatibility** | `test_compat_no_series_id` | GlossaryBuilder without series_id works | Works identically to baseline |
| **Fail-Closed** | `test_fail_closed_all_paths` | All validation paths throw exceptions | No fallback defaults |

---

## 20. Validation Gates

**All must PASS before Batch 5.4 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-03 + SG-01~15 tests PASS
- [ ] Batch 5.4 Acceptance Test Matrix (§19) all PASS
- [ ] No regression in existing pytest tests (GlossaryBuilder, Glossary, GlossaryContext, EntityResolver, Series Identity, Series Memory, Series Entity)
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 21. Git Scope Rules

**Allowed Changes:**

- **ADDITIVE** `core/glossary_builder.py` — Three new functions, new dataclasses, new exceptions, persistence helpers
- **ADDITIVE** `core/series_identity/manifest.py` — Add `series_glossary_hash` derived field (following `series_memory_hash` pattern)
- **ADDITIVE** `core/series_identity/registry.py` — Add `update_series_glossary_hash()` method
- **NEW** `tests/series/test_batch5_4_*.py` (test files)
- **NEW** `docs/governance/rm8/series_glossary_contract.md` (contract doc)

**Forbidden:**

- Any modification to existing production code outside allowed additive changes
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 22. Delivery Rules

**Deliverables (working tree changes only, no staging):**

1. Extended `core/glossary_builder.py` with Series Glossary functions
2. Additive changes to `core/series_identity/manifest.py` — `series_glossary_hash` derived field
3. Additive changes to `core/series_identity/registry.py` — `update_series_glossary_hash()` method
4. `tests/series/test_batch5_4_*.py`
5. `docs/governance/rm8/series_glossary_contract.md`
6. Updated `P0_STAGE5_FORMAL_SPECIFICATION.md` (if any spec clarifications needed)
7. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 23. Rollback Boundary

**Clean Rollback:**

- Revert `core/glossary_builder.py` to baseline
- Revert `core/series_identity/manifest.py` to baseline
- Revert `core/series_identity/registry.py` to baseline
- Delete `tests/series/test_batch5_4_*.py`
- Delete `docs/governance/rm8/series_glossary_contract.md`

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules
- **Frozen glossary files UNCHANGED — no revert needed**

---

## 24. Provider / Network / Translation Policy

- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation only

---

## 25. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/glossary_builder.py` — implementation (extended)
- `core/series_identity/manifest.py` — additive manifest field
- `core/series_identity/registry.py` — additive registry method
- `tests/series/` — tests
- `docs/governance/rm8/` — docs/contracts
- `artifacts/` — diagnostic output only

---

## 26. Completion Criteria

**Batch 5.4 Complete When:**

1. All §18 unit tests PASS
2. All §18 property-based tests PASS (1000 iterations each)
3. All §18 CSI-03 + SG-01~15 tests PASS
4. All §19 Batch 5.4 Acceptance Test Matrix PASS
5. Validation gates (§20) all PASS
6. Git status shows only allowed new files + allowed additive changes
7. No production code modified outside allowed additive changes
8. No Frozen Contracts modified
9. **Frozen glossary components unchanged** (glossary.py, glossary_context.py, glossary_resource.py)

**Status Report:** "P0 Stage 5 Batch 5.4 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 27. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Preflight complete, models defined, integration points specified, Owner decisions incorporated | 2026-08-20 |
| Owner | Authorization to proceed | ____________ |
| QA | CSI-03 + SG-01~15 test matrix & Acceptance Test Matrix accepted | ____________ |

---

## 28. Owner Decisions — FROZEN (Owner Confirmed 2026-08-20)

All decisions below are **OWNER-CONFIRMED and FROZEN** for Batch 5.4 implementation.

| Decision | Options | FROZEN Choice |
|----------|---------|---------------|
| **SG-1: Term Selection Scope** | All books vs completed books only | **Completed books only** (status=completed/promoted) — FROZEN |
| **SG-2: Confidence Threshold** | ≥0.95 vs ≥0.90 vs configurable | **≥0.95** — FROZEN |
| **SG-3: Locked Term Definition** | `locked=True` only vs `locked=True` OR `confidence>=0.95` | **Both locked AND high-confidence** — FROZEN |
| **SG-4: Promotion Scope** | Locked terms only vs locked + high-confidence | **Both locked and high-confidence (MANUAL gate)** — FROZEN |
| **SG-5: Glossary Builder Modification** | New module vs extend glossary_builder.py | **Extend glossary_builder.py** (no new module) — FROZEN |
| **SG-6: Frozen Component Integration** | Modify glossary.py/glossary_context.py vs adapter pattern | **Adapter pattern only** — FROZEN. No changes to FROZEN files. |

---

*End of Batch 5.4 Implementation Task. Specification FINALIZED — Ready for Implementation Authorization.*