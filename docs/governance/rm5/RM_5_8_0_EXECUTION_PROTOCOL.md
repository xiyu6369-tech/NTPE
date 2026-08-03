# RM-5.8.0 — Benchmark Execution Protocol

## Overview

This document defines **when** and **how** benchmarks must be executed. The protocol ensures consistent, repeatable benchmark runs and establishes the regression detection framework.

---

## Execution Triggers

Benchmarks **MUST** be re-run when ANY of the following change:

| Trigger Category | Specific Changes |
|------------------|------------------|
| **Prompt** | System prompt, user prompt, extraction prompt, few-shot prompt |
| **Few-shot** | Example selection, example ordering, example count, example format |
| **Extractor** | Extractor logic, entity schema, output format, post-processing |
| **Schema** | JSON schema modifications, field additions/removals, constraint changes |
| **Validation Rule** | Schema validation rules, business rule definitions, cross-field rules |
| **Review Rule** | Auto-review criteria, confidence thresholds, escalation rules |
| **Compilation** | Package compilation logic, serialization format, checksum algorithm |
| **Model** | Model provider, model version, temperature, top-p, max tokens |

**Rule**: Any change to the above requires a full benchmark run before merge/deployment.
---

## Execution Modes

### 1. Full Benchmark (Mandatory)
- **Scope**: All 5 extractors, all 3 difficulty tiers
- **When**: Any trigger from above list
- **Duration Target**: < 30 minutes
- **Output**: Complete Scorecard + Regression Report

### 2. Targeted Benchmark (Optional)
- **Scope**: Specific extractor(s) affected by change
- **When**: Minor prompt tweaks, single-extractor changes
- **Duration Target**: < 10 minutes
- **Output**: Partial Scorecard (affected extractors only)

### 3. Smoke Benchmark (CI/CD Gate)
- **Scope**: 1 easy case per extractor (5 total)
- **When**: Every PR merge to main
- **Duration Target**: < 2 minutes
- **Output**: Pass/Fail only (no detailed scores)

---

## Execution Environment

| Requirement | Specification |
|-------------|---------------|
| **Isolation** | Separate process, no shared state with runtime |
| **Network** | Zero outbound requests (offline mode) |
| **Providers** | Zero provider API calls |
| **Determinism** | Fixed seed, no randomness in metric computation |
| **Artifacts** | All outputs written to `benchmarks/results/current/` |

---

## Pre-Execution Checklist

- [ ] Golden dataset version recorded
- [ ] Baseline version identified (for regression comparison)
- [ ] Configuration hash recorded (prompt version, few-shot version, model)
- [ ] Runtime version recorded (knowledge extraction pipeline version)
- [ ] Environment clean (no stale artifacts in `results/current/`)

---

## Execution Steps

```
1. VALIDATE ENVIRONMENT
   ├── Check golden dataset exists and is valid
   ├── Check baseline exists for comparison
   └── Verify no network access

2. LOAD GOLDEN DATASET
   ├── Read all entries from benchmarks/golden/
   ├── Validate schema compliance
   └── Group by extractor and difficulty

3. RUN EXTRACTION (via Runtime)
   ├── For each golden entry:
   │   ├── Feed input.text to Knowledge Extraction Runtime
   │   ├── Capture Knowledge Package output
   │   └── Store for comparison
   └── Record extraction metadata (timing, versions)

4. COMPUTE METRICS
   ├── For each extractor:
   │   ├── Match extracted entities to golden entities
   │   ├── Compute all metrics per RM_5_8_0_METRICS.md
   │   └── Aggregate per difficulty tier
   └── Compute overall scores

5. GENERATE SCORECARD
   ├── Format per RM_5_8_0_SCORECARD.md
   ├── Include regression comparison
   └── Write to benchmarks/results/current/scorecard.md

6. REGRESSION CHECK
   ├── Load baseline from benchmarks/results/baseline/
   ├── Compare F1 per extractor
   ├── Flag any regression > threshold
   └── Write regression report

7. ARCHIVE RESULTS
   ├── Copy current/ to history/{timestamp}/
   ├── Update baseline if approved (manual step)
   └── Clean current/ for next run
```

---

## Regression Thresholds

| Metric | Regression Threshold | Action |
|--------|---------------------|--------|
| **F1 (per extractor)** | Drop > 0.02 (2 pp) | BLOCK merge, require investigation |
| **Overall Score** | Drop > 0.015 (1.5 pp) | BLOCK merge, require investigation |
| **Schema Pass Rate** | Any drop | BLOCK merge |
| **Compilation Success** | Any drop | BLOCK merge |
| **Deterministic Rebuild** | Any drop | BLOCK merge |

**Note**: Thresholds are absolute drops from baseline, not relative.

---

## Baseline Management

### Creating Baseline
```bash
# After successful benchmark with acceptable scores:
cp benchmarks/results/current/ benchmarks/results/baseline/v1.0.0/
# Record: golden_version, config_hash, timestamp, approver
```

### Baseline Immutability
- Baselines are **immutable** once created
- New baseline = new version directory (v1.0.1, v1.1.0, etc.)
- Each baseline bound to specific golden dataset version

### Baseline Retention
- Keep last 10 baselines
- Archive older to cold storage

---

## CI/CD Integration

```yaml
# .github/workflows/benchmark.yml
name: Knowledge Benchmark

on:
  pull_request:
    paths:
      - 'core/knowledge/**'
      - 'prompt_packages/**'
      - 'schemas/knowledge/**'
      - 'config/knowledge/**'

jobs:
  benchmark-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Smoke Benchmark
        run: python -m benchmarks.run_smoke
      - name: Check Pass/Fail
        run: cat benchmarks/results/current/smoke_result.txt

  benchmark-full:
    if: github.event_name == 'pull_request' && github.base_ref == 'main'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Run Full Benchmark
        run: python -m benchmarks.run_full
      - name: Upload Scorecard
        uses: actions/upload-artifact@v4
        with:
          name: scorecard
          path: benchmarks/results/current/scorecard.md
      - name: Regression Check
        run: python -m benchmarks.check_regression
```

---

## Manual Execution Commands

```bash
# Full benchmark
python -m benchmarks.run_full --golden v1.0.0 --config prompt_v2.1

# Targeted benchmark (character only)
python -m benchmarks.run_targeted --extractor character --golden v1.0.0

# Smoke benchmark
python -m benchmarks.run_smoke --golden v1.0.0

# Regression check only (against existing results)
python -m benchmarks.check_regression --baseline v1.0.0 --current current
```

---

## Acceptance Criteria for This Document

- [ ] All 8 trigger categories defined
- [ ] Three execution modes specified
- [ ] Environment requirements defined
- [ ] Step-by-step execution flow documented
- [ ] Regression thresholds specified
- [ ] Baseline management process defined
- [ ] CI/CD integration example provided
- [ ] Manual commands documented