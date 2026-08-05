# RM-5.8.5 — Regression Gate Policy

## Overview

This document defines the regression detection thresholds and gate logic for the NTPE Knowledge Benchmark System.

The regression gate ensures that no release introduces quality degradation beyond defined tolerance levels.

---

## Regression Thresholds

| Metric | Warning Threshold | Fail Threshold | Direction |
|--------|------------------|----------------|-----------|
| **F1 Score** | < 0.05% drop | < 1.0% drop | Lower is worse |
| **Precision** | < 0.1% drop | < 2.0% drop | Lower is worse |
| **Recall** | < 0.1% drop | < 2.0% drop | Lower is worse |
| **ECE** | < 0.1% rise | < 2.0% rise | Higher is worse |
| **Missing Rate** | < 0.1% rise | < 2.0% rise | Higher is worse |
| **Hallucination Rate** | < 0.1% rise | < 2.0% rise | Higher is worse |
| **Schema Pass Rate** | < 0.2% drop | < 5.0% drop | Lower is worse |
| **Business Rule Pass** | < 0.2% drop | < 5.0% drop | Lower is worse |

---

## Gate Status

| Status | Meaning | Release Allowed? |
|--------|---------|-----------------|
| **PASS** | All metrics within acceptable range | Yes |
| **WARNING** | Some metrics degraded but below fail threshold | Yes (with caution) |
| **FAIL** | One or more metrics exceeded fail threshold | **No** |

---

## How It Works

```
Current Scorecard         Baseline Entry
       │                       │
       └───────────┬───────────┘
                   ▼
          Regression Gate
                   │
                   ▼
        ┌──────────────────┐
        │ Compare per metric │
        │ per extractor      │
        └──────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    PASS / WARNING          FAIL
        │                     │
        ▼                     ▼
  Allow Release         Block Release
```

---

## Regression Report

Each evaluation produces a `RegressionGateReport`:

- `overall_status`: PASS, WARNING, or FAIL
- `comparisons`: Per-extractor, per-metric comparison
- `failure_count`: Number of metrics with FAIL status
- `warning_count`: Number of metrics with WARNING status
- `pass_release`: True only if overall_status is not FAIL

---

## Delta Calculation

For **standard metrics** (F1, Precision, Recall, Schema/Business Pass):
```
delta = baseline_value - current_value
```

For **inverted metrics** (ECE, Missing Rate, Hallucination Rate):
```
delta = current_value - baseline_value
```

A positive delta means **regression** (worsening).

---

## Governance Rules

1. **Gate must pass for release** — any FAIL blocks release
2. **Thresholds are configurable** — per policy, not hardcoded judgment
3. **Baseline comparison only** — no baseline = no regression check
4. **Per-extractor evaluation** — each extractor is independently checked
5. **Report is permanent** — regression gate reports are archived

---

## Related

- `RM_5_8_5_BASELINE_POLICY.md` — Baseline management
- `RM_5_8_5_DASHBOARD_SPEC.md` — Dashboard format
- `core/knowledge_benchmark/regression_gate.py` — Implementation

---

## Version

RM-5.8.5 — Knowledge Benchmark Regression Gate Policy