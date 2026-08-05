# RM-5.9.0 Runtime Cache Policy

**Version**: RM-5.9.0  
**Date**: 2026-08-06  
**Status**: 🔒 **FROZEN — Governance Policy**

---

## Purpose

Define the lifecycle, scope, and invalidation rules for the knowledge runtime cache. The cache is an optimization (no knowledge structure is duplicated), respecting the read-only contract and must never mutate the frozen package.

---

## 1. Cache Architecture

### 1.1 Cache Model

```
┌───────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE RUNTIME CACHE                       │
│                     (per-session, in-memory, read-only)            │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Character Cache │  │ Glossary Cache  │  │ Scene Cache     │  │
│  │ (per-volume)    │  │ (per-volume)    │  │ (per-chapter)   │  │
│  │                 │  │                 │  │                 │  │
│  │ entity_id →     │  │ term →          │  │ chapter_id →    │  │
│  │   Character[]   │  │   Glossary[]    │  │   Scene[]       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │ Narrative Cache │  │ Style Cache     │                          │
│  │ (per-chapter)   │  │ (per-volume)    │                          │
│  │                 │  │                 │                          │
│  │ chapter_id →    │  │ per-volume →    │                          │
│  │   Narrative[]   │  │   StyleRule[]   │                          │
│  └─────────────────┘  └─────────────────┘                          │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                     PACKAGE MIRROR                          │  │
│  │  characters[]  glossaries[]  scenes[]  narrative[]  style[] │  │
│  │  manifest.json  package.json                                │  │
│  │  (loaded once, verified based on checksum)                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 Cache Properties

| Property | Value | Rationale |
|----------|-------|-----------|
| **Storage** | In-memory Python dictionaries | No disk I/O during translation |
| **Mutability** | Read-only (cache is a mirror, not a database) | Must match package snapshot |
| **Concurrency** | Single-thread (no synchronization needed) | Translation is single-threaded per session |
| **Size** | Bounded by package entity count | Same as JSON file; no additional serialization |

---

## 2. Package Loading Lifecycle

### 2.1 Load Sequence

```
Session Start
    │
    ▼
KnowledgePackageProvider.__init__(package_dir)
    │
    ├── 1. Load package.json
    ├── 2. Verify SHA-256 checksum (manifest.sha256 = computed)
    ├── 3. If checksum mismatch → abort (corruption)
    ├── 4. Load 5 entity files (json.load) into mem arrays
    ├── 5. Build per-domain lookup indices
    │       characters:  entity_id → Character[]
    │       glossary:     term → GlossaryEntry[]
    │       scenes:       chapter_id → Scene[]
    │       narrative:    chapter_id → Narrative[]
    │       style:        genre → StyleRule[]
    ├── 6. Mark provider as verified
    ├── 7. Publish to Cache machine
    │
    └── Session ready (chunk N await)
```

### 2.2 Reload Trigger

| Trigger | Action | Cache Effect |
|---------|--------|-------------|
| **Manual reload** (user action) | `provider.reload()` | Full cache deletion + reload all files |
| **Volume switch** | New package path → new provider | Full cache deletion + reload all files |
| **External update detected** | checksum change in manifest | Full cache deletion if `auto_reload = True` (default); warn if `auto_reload = False` |
| **Never — translation cycle** | During translation | Cache is stable during entire session unless explicitly reloaded |

---

## 3. Cache Lifetime

### 3.1 Lifetable by Domain

| Cache | Lifetime | Invalidated By |
|-------|----------|----------------|
| **Character** | Per-volume | Volume switch, package refresh |
| **Glossary** | Per-volume | Volume switch, package refresh |
| **Scene** | Per-chapter | Chapter boundary, volume switch, package refresh |
| **Narrative** | Per-chapter | Chapter boundary, volume switch, package refresh |
| **Style** | Per-volume | Volume switch, package refresh |

### 3.2 Lifetime Rationale

| Domain | Lifetime Reason |
|--------|----------------|
| Character | Characters are consistent across the entire volume. Same character appears in chapters 1-50 with same `canonical_name`, `role`, `traits`. Per-volume cache is correct. |
| Glossary | Terminology is consistent per-novel. A glossary term in chapter 5 means the same thing in chapter 32. |
| Scene | Scenes are tied to their chapter. Chapter change invalidates the scene context. The Scene[] for chapter 6 is irrelevant when translating chapter 7. |
| Narrative | Plot points and timeline position are per-chapter. After a chapter = "%part" change, the narrative cache is stale. |
| Style | Style is per-volume — the author's writing style may differ between volumes but not between chapters. |

---

## 4. Cache Invalidation

### 4.1 Invalidation Types

| Type | Triggers | Domains Invalidated |
|------|----------|---------------------|
| **Full invalidation** | Package reload, volume switch, periodic checksum change | ALL (5 domains + package mirror) |
| **Partial invalidation** | Chapter boundary detected | Scene + Narrative (2 domains) |
| **No invalidation** | Same chapter, same scene | 0 domains (hot cache reuse) |

### 4.2 Chapter Boundary Detection

```python
def detect_chapter_boundary(previous_chunk: ChunkProfile, current_chunk: ChunkProfile) -> bool:
    """Chapter boundary detected when chapter_id changes between two consecutive chunks."""
    return previous_chunk and current_chunk.chapter_id != previous_chunk.chapter_id
```

When detected:
- Scene cache cleared: `cache.scene.clear()`
- Narrative cache cleared: `cache.narrative.clear()`
- Character, Glossary, Style — retained

### 4.3 Volume Switch Detection

Volume switch is either:
- Manual trigger (user switches volume input file)
- Detected by `volume_id` change in chunk metadata

Both trigger **full invalidation**.

### 4.4 Checksum Change Detection

```python
def check_package_freshness(provider, last_checksum: str) -> str | None:
    current_checksum = provider.package["checksum"]
    if current_checksum != last_checksum:
        return current_checksum  # new checksum → reload needed
    return None
```

Package checksum change is a protection against:
- External tool recompiling the knowledge package
- Filesystem corruption
- Version bump

---

## 5. Chapter Switching

### 5.1 Inline Cache Management for Chapter Boundary

```
Before:    Chunk K         Chunk K+1         Chunk K+2
           chapter=X       chapter=X         chapter=Y  ← boundary

Cache:    char cache loaded,  scene(X) in mem,  narrative(X) in mem
After:    Attention: Inval scene → reload chapter Y, narrative → reload chapter Y
          char/glossary/style unchanged
```

### 5.2 Per-chapter query after invalidation

When scene/narrative cache is invalidated at chapter switch, the next chunk performs:

1. Check cache → miss (fresh)
2. Query provider for scene entries matching new chapter ID
3. Query provider for narrative entries matching new chapter ID
4. Populate cache
5. Subsequent chunks in same chapter → cache hit

---

## 6. Volume Switch

### 6.1 Full Cache Flush

```
Session
    │ user switches from Vol 1 → Vol 2
    │
    ▼
Invalidate ALL caches (5 domains + package mirror)
    │
    ▼
Load new package (vol_2/v1/package.json)
    │
    ▼
Verify checksum → populate all 5 caches fresh
    │
    ▼
Continue session from chunk 0 of vol 2
```

---

## 7. Read-Only Guarantee

### 7.1 Mirroring Rule

The cache is a **mirror** of the frozen package — never a source of truth.

| Operation | Allowed? | Reasoning |
|-----------|----------|-----------|
| Read entity from cache | ✅ | Cache is mirror |
| Return entity from cache | ✅ | Returned data is immutable snapshot |
| Write to cache (update entity) | ❌ | Violates read-only contract |
| Modify entity in cache | ❌ | Violates read-only contract |
| Persis cache to disk | ❌ | Cache is session-only; package does not mutate |
| Programmatic modification of cache | ❌ | Cache never overrides original package |
| Programmatic write to package directory | ❌ | Physical immutable package in filesystem |

### 7.2 Cache Session Isolation

Multiple translation sessions operate with **independent** cache instances — no shared mutable cache.

---

## 8. Cache Statistics (Metadata)

At session end, cache statistics captured:

```json
{
  "cache_policy": "rm-5.9.0",
  "cache_write_hit": 95.6,
  "cache_miss_events": 3,
  "cache_invalidation_triggers": 2,
  "cache_invalidation_full": 1,
  "cache_invalidation_partial": 1,
  "cache_invalidation_members": ["Scene", "Narrative"],
  "cache_domain_sizes": {
      "character": 85,
      "glossary": 204,
      "scene": 48,
      "narrative": 12,
      "style": 3
  }
}
```

---

## 9. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_9_0_RUNTIME_INTEGRATION_ARCHITECTURE.md` | Parent architecture |
| `RM_5_9_0_PROMPT_INJECTION_POLICY.md` | Injection order |
| `RM_5_9_0_CONTEXT_BUDGET_POLICY.md` | Token allocation |
| `RM_5_9_0_RUNTIME_SEQUENCE.md` | Sequence diagrams |

---

*This policy is FROZEN as of RM-5.9.0 (2026-08-06).*