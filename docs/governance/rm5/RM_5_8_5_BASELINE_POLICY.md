# RM-5.8.5 — Baseline Management Policy

## Overview

This document defines how benchmark baselines are established, promoted, managed, and rolled back for the NTPE Knowledge Benchmark System.

Baselines serve as the reference point for regression detection and release gating.

---

## Baseline Lifecycle

```
 ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
 │  Current     │──────▶  Promoted    │──────▶  Active      │
 │  Results     │      │  (Staged)   │      │  (Reference) │
 └─────────────┘      └─────────────┘      └─────────────┘
                                                  │
                                           ┌──────┴──────┐
                                           ▼              ▼
                                    ┌──────────┐  ┌──────────────┐
                                    │ Rollback  │  │  Archived     │
                                    │ (Previous)│  │  (Historical) │
                                    └──────────┘  └──────────────┘
```

---

## Promoting a Baseline

Baselines are promoted from `benchmarks/results/current/` when the team determines the current benchmark results reflect the desired quality standard.

**Promotion criteria**:
1. All extractors have run successfully
2. No extraction errors
3. Overall score meets or exceeds `0.70`
4. Regression checks against previous baseline pass

**Command**:
```bash
python -m tools.knowledge_benchmark.cli --promote-baseline
```

**Storage**:
```
benchmarks/results/baseline/
├── baseline_index.json          # Index with active/previous pointers
├── baseline_YYYYMMDD_HHMMSS_XXXX.json  # Per-baseline metadata
├── character_scorecard.json
├── glossary_scorecard.json
├── scene_scorecard.json
├── narrative_scorecard.json
├── style_scorecard.json
└── overall_scorecard.json
```

---

## Baseline Index

The `baseline_index.json` tracks:

| Field | Description |
|-------|-------------|
| `entries` | List of all baselines (ordered) |
| `active_id` | Current active baseline ID |
| `previous_id` | Previous baseline ID (for rollback) |

Each entry contains:
- `baseline_id`: Unique ID
- `run_id`: Source benchmark run
- `overall_score`: Aggregate score
- `grade`: Letter grade (A+, A, B, C, F)
- `extractor_scores`: Per-extractor score map
- `metric_snapshots`: Individual metric values
- `status`: `active`, `promoted`, `rolled_back`, `archived`
- `content_hash`: Immutable verification hash

---

## Rollback

If a newly promoted baseline is found to be incorrect or if regression analysis indicates quality degradation, the previous baseline can be restored.

**Constraints**:
- At least 2 baselines must exist
- Returns the **second-to-last** baseline

---

## Operations

| Operation | Description |
|-----------|-------------|
| `list_baselines()` | List all baselines with status |
| `load_baseline()` | Load active or specific baseline |
| `promote()` | Promote current to baseline |
| `rollback()` | Revert to previous baseline |

---

## Governance Rules

1. **Promotion is additive** — baselines are never deleted
2. **Immutable after promotion** — baseline data is frozen
3. **Rollback preserves history** — previous baselines remain accessible
4. **Content hashing** — each baseline is verifiable via SHA-256
5. **No overwrite** — each baseline is a separate file

---

## Version

RM-5.8.5 — Knowledge Benchmark Baseline Management