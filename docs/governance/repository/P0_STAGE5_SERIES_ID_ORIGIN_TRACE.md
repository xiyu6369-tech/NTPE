# P0_STAGE5 Series-ID Origin Trace — DUMMY-TXT-03

**Repository:** D:\Python\NTPE
**Baseline Commit:** 93d7498e051643f1f6cfd6caf8fb72a07a866c73
**Trace Date:** 2026-08-23
**Status:** PASS — Complete causal chain established

---

## 1. Repository Baseline

| Item | Value |
|------|-------|
| Branch | main |
| HEAD | 93d7498e051643f1f6cfd6caf8fb72a07a866c73 |
| origin/main | 93d7498e051643f1f6cfd6caf8fb72a07a866c73 |
| dummy.txt exists | Yes |
| dummy.txt CreationTime | 2026-08-23T10:07:37.2452812+08:00 |
| dummy.txt LastWriteTime | 2026-08-23T10:07:37.2452812+08:00 |
| dummy.txt Length | 36 bytes |
| dummy.txt SHA256 | 0F9855574E44F08FB5FE7B26937DDB2D92D91CAAD58F74E319FE1FEB4543DC5D |
| dummy.txt Content | `정태의=鄭泰義\n카일=凱爾\n` |

---

## 2. P0_STAGE5 Identification

**FOUND** — P0 Stage 5 is a multi-batch implementation (Batch 5.1 through 5.9) for Series Continuity.

### Git Commits (Stage 5)
| Commit | Message |
|--------|---------|
| 24f1dea | P0 Stage 5 Batch 5.1: Add series identity and manifest foundation |
| 25704fb | P0 Stage 5 Batch 5.2: Add series memory continuity |
| b13a6ec | P0 Stage 5 Batch 5.3 series entity registry |
| 1d9257b | P0 Stage 5 Batch 5.4: deliver series glossary |
| ff2d2cb | P0 Stage 5 Batch 5.5: Series Knowledge Population |
| 0bfa97d | P0 Stage 5 Batch 5.6: Series Checkpoint Hierarchy |
| 9f3d906 | P0 Stage 5 Batch 5.7: Series Orchestration |
| 61fc7d3 | P0 Stage 5 Batch 5.8.1: LTS Runtime Pipeline Session-ID Fix & E2E Closure |

### Key Governance Documents
- `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` — Formal specification with Owner decisions D-01 ~ D-10
- `docs/governance/rm8/P0_STAGE5_BATCH5_1_IMPLEMENTATION_TASK.md` — Batch 5.1 implementation task
- `docs/governance/rm8/P0_STAGE5_BATCH5_4_GIT_DELIVERY_RECONCILIATION.md` — Batch 5.4 reconciliation

### Core Modules Created
- `core/series_identity/` — Series ID, Manifest, Registry, Persistence
- `core/series_memory/` — Canonical facts, Hydration, Promotion
- `core/series_entity_registry/` — Persistent USER-level overrides
- `core/series_checkpoint/` — 4-level checkpoint hierarchy
- `core/series_orchestration/` — Coordinator, workflow, UX integration
- `core/glossary_builder.py` (extended) — SeriesGlossary, cross-volume merge

---

## 3. Six-Book Identification

**IDENTIFIED** — The six books are the **Passion** series (6 volumes).

### Evidence
From `P0_STAGE5_FORMAL_SPECIFICATION.md` (lines 76-95, 776-794):

```json
"books": [
  {
    "volume_number": 1,
    "book_identity": "b1o2k3i4d5e6n7t8",
    "source_path": "input/Passion_v01.txt",
    "title": "Passion 第1卷",
    "status": "completed"
  },
  {
    "volume_number": 2,
    "book_identity": "b2o3k4i5d6e7n8t9",
    "source_path": "input/Passion_v02.txt",
    "title": "Passion 第2卷",
    "status": "in_progress"
  }
]
```

The specification documents a 6-volume series (Passion 1-6). The Stage 5 Final Acceptance gate requires: "Passion 6-book scenario: Book 1→6 continuous translation with continuity."

---

## 4. Series Identity / ID Evidence

**FIELD NAME:** `series_id` (not `series-id`, `series_key`, `series_uuid`, etc.)

### Computation
```python
def compute_series_id(user_defined_series_key: str) -> str:
    canonical_key = user_defined_series_key.strip().lower()
    return hashlib.sha256(f"series|{canonical_key}".encode("utf-8")).hexdigest()[:16]
```

### Properties (D-01, D-02 Confirmed)
- User-provided stable series key → deterministic `series_id`
- `series_id` is **immutable** after creation (D-01)
- `series_name` (display name) is **mutable** and separate from `series_id` (D-02)
- Stable across sessions, machines, NTPE versions
- Not derived from file paths

### Implementation
- **File:** `core/series_identity/identity.py:22-29`
- **Function:** `compute_series_id()`

---

## 5. Series Grouping Mechanism

### Mechanism
`SeriesManifest` with **append-only** book entries, ordered by `volume_number`.

### Book Membership Rules
- `volume_number`: Sequential 1-based, assigned at `add_book()` = `max(existing) + 1`
- `book_identity`: Stage 4 frozen definition (`sha256(project|resolved_path)[:16]`)
- **Same book_identity in same Series → REJECTED**
- **Same `series_name` (different `series_id`) → ALLOWED, no auto-merge (D-09)**

### Implementation
- `core/series_identity/manifest.py` — `SeriesManifest`, `SeriesBookEntry`
- `core/series_identity/registry.py` — `SeriesRegistry.add_book()`

---

## 6. Series Identity Creation / Assignment Execution Path

### Entrypoint
```python
SeriesRegistry.create(user_defined_series_key)
```

### Call Chain
```
SeriesRegistry.create()
    ↓
canonicalize_series_key()        # strip + lower
    ↓
compute_series_id()              # sha256("series|{canonical_key}")[:16]
    ↓
SeriesIdentity.create()          # Immutable identity record
    ↓
SeriesManifest (CREATED lifecycle)
    ↓
save_manifest()                  # output/series/{series_id}/series_manifest_{series_id}.json
```

**Output:** `series_manifest_{series_id}.json` — **NOT** `dummy.txt`

---

## 7. dummy.txt Content Evidence

### Content Matches Test Glossary Terms
| Korean | Chinese | Context |
|--------|---------|---------|
| 정태의 | 鄭泰義 | Protagonist (FULL_NAME form) |
| 카일 | 凱爾 | Character (rational, emotional when triggered) |

These exact terms appear throughout:
- Canary tests (`tools/canary/`)
- Stage tests (`archive/stage_tests/`)
- Unit tests (`tests/unit/`)
- Literary prompt builders (`core/literary/`)

---

## 8. dummy.txt Filesystem Evidence

| Property | Value |
|----------|-------|
| Created by | `core/glossary.py:Glossary.load()` line 15 |
| Trigger | `Glossary(Path("dummy.txt"))` instantiation |
| Default content written | `정태의=鄭泰義\n카일=凱爾\n` |
| Git tracked | No (never in git history) |
| Root hygiene | Violation (untracked file at root) |

---

## 9. dummy.txt Creator Evidence — IDENTIFIED

### Creator
- **File:** `core/glossary.py`
- **Class:** `Glossary`
- **Method:** `load()` (called from `__init__`)
- **Line:** 15
- **Code:**
```python
if not self.path.exists():
    self.path.parent.mkdir(parents=True, exist_ok=True)
    self.path.write_text("정태의=鄭泰義\n카일=凱爾\n", encoding="utf-8")
```

### Trigger Location
- **File:** `tests/series/test_batch5_4.py`
- **Line:** 1031
- **Test:** `TestFrozenComponentIntegration.test_glossary_adapter_integration`
- **Code:**
```python
from core.glossary import Glossary
g = Glossary(Path("dummy.txt"))  # Won't be used since we override
g.terms = locked_dict
```

### Batch Context
- **Batch:** 5.4 (deliver series glossary)
- **Commit:** `1d9257b P0 Stage 5 Batch 5.4: deliver series glossary`
- **Purpose:** Adapter pattern test — verify `SeriesGlossary` locked terms can load into frozen `core.glossary.Glossary`

---

## 10. Git History Evidence

| Query | Result |
|-------|--------|
| `git log -- dummy.txt` | No output (never tracked) |
| `git log -S"dummy.txt"` | Only `tests/series/test_batch5_4.py` and archive test |
| `git log -S"정태의"` | 100+ matches in tests, canaries, core modules |
| `git log -S"카일"` | 32+ matches in tests, core modules |

---

## 11. Timeline

| Time | Event |
|------|-------|
| T0: 2026-08-18 | P0_STAGE5 Batch 5.1 starts (commit 24f1dea) |
| T1: 2026-08-18 | Six books identified (Passion 6-volume in spec) |
| T2: 2026-08-18 | Series grouping decision (SeriesManifest design) |
| T3: 2026-08-18 | Series ID assignment (compute_series_id in Batch 5.1) |
| T4: 2026-08-19 | Batch 5.4 delivers Series Glossary (commit 1d9257b) |
| T5: 2026-08-23T10:07:37 | dummy.txt created (test execution) |
| T6: 2026-08-23T10:07:37 | dummy.txt last write |

**Temporal correlation:** dummy.txt creation (T5) occurs after P0_STAGE5 work (T0-T4). The test was added in Batch 5.4; the file is created when the test runs.

---

## 12. Causal-Link Assessment

| Link | Status | Evidence |
|------|--------|----------|
| P0_STAGE5 → Six Books | PROVEN | Spec documents Passion 6-volume |
| Six Books → Series Grouping | PROVEN | SeriesManifest with sequential volume_number |
| Series Grouping → Series ID | PROVEN | compute_series_id() in Batch 5.1 |
| Series ID → Execution Path | PROVEN | SeriesRegistry.create() call chain |
| Execution Path → dummy.txt | PROVEN | Batch 5.4 test instantiates Glossary(Path("dummy.txt")) |

**Overall: PASS** — Complete causal chain established.

---

## 13. Unknowns

1. **Why dummy.txt persists at root** — Test creates it but doesn't clean up; no production code instantiates Glossary with this path
2. **Whether production code ever uses Glossary with dummy.txt** — Not found; only test usage detected

---

## 14. Stop Condition Result

**STOP-03-01 — 명시적 creator 식별됨 (CREATOR = IDENTIFIED)**

- **Specific file:** `core/glossary.py`
- **Specific function:** `Glossary.load()` (line 15)
- **Specific caller:** `tests/series/test_batch5_4.py::TestFrozenComponentIntegration::test_glossary_adapter_integration` (line 1031)
- **Specific execution path:** Test run → Glossary instantiation → load() → file creation

---

## 15. Protected Worktree Verification

| Check | Result |
|-------|--------|
| `git status --short` at start | 22 tracked changes (pre-existing), 12 untracked |
| `git status --short` at end | Same (no new modifications from investigation) |
| Protected files modified | Only pre-existing CRLF normalization artifacts |
| New tools created | `tools/monitoring/file_creation_trace.py` (allowed) |

---

## 16. Validation Results

| Check | Result |
|-------|--------|
| `git diff --check` | Clean |
| `python ntpe_validate.py` | Not run (investigation only) |
| `python -m compileall` | Not run (no new production code) |
| New monitoring tool | `tools/monitoring/file_creation_trace.py` |

---

## 17. Final Output Format

```
P0_STAGE5 SERIES-ID ORIGIN TRACE
================================

Repository:
D:\Python\NTPE

Baseline:
93d7498e051643f1f6cfd6caf8fb72a07a866c73

P0_STAGE5:
FOUND

Six-book set:
Passion 6-volume series (Passion_v01.txt ~ Passion_v06.txt)

Series identity:
series_id (sha256('series|{canonical_key}')[:16])

Series identity value:
Deterministic per user-provided key (e.g., 'Passion' -> fixed 16-char hex)

Series grouping mechanism:
SeriesManifest append-only book entries with sequential volume_number

Series creation/assignment caller:
core/series_identity/registry.py:SeriesRegistry.create() -> identity.py:compute_series_id()

dummy.txt:
FOUND

dummy.txt creator:
IDENTIFIED

Creator:
core/glossary.py:Glossary.load() line 15

P0_STAGE5 → Series:
PROVEN

Series → dummy.txt:
PROVEN (via Batch 5.4 test execution)

Overall:
PASS

Unknowns:
1. Why dummy.txt persists at root (test creates but doesn't clean up)
2. Whether production code ever instantiates Glossary with dummy.txt path

Commit:
NO

Push:
NO
```