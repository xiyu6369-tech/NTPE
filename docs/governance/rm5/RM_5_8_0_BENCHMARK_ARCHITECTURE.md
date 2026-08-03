# RM-5.8.0 — Knowledge Benchmark Architecture

## Overview

This document defines the **Knowledge Layer Benchmark Architecture** for NTPE. The benchmark framework is designed to provide a repeatable, quantifiable, and comparable way to validate the quality of all Knowledge Extractor, Prompt, Few-shot, and Model changes.

**Critical Constraint**: This framework is completely separated from the Translation Runtime and Knowledge Runtime. It does not modify any frozen architecture from RM-5.7.

---

## Architecture Separation

```
┌─────────────────────────────────────────────────────────────────┐
│                        NTPE RUNTIME                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Translation     │  │ Knowledge       │  │ Knowledge       │  │
│  │ Engine          │  │ Extraction      │  │ Validation      │  │
│  │ (FROZEN)        │  │ (FROZEN)        │  │ (FROZEN)        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BENCHMARK FRAMEWORK                          │
│  (Separate Process — No Runtime Dependency)                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Golden       │  │ Benchmark    │  │ Scorecard    │          │
│  │ Dataset      │──▶│ Metrics      │──▶│ Generator    │          │
│  │              │  │ Engine       │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Regression Protocol                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---
---

## Component Definitions

### 1. Golden Dataset
- **Location**: `benchmarks/golden/`
- **Structure**: Per-extractor directories with difficulty tiers
- **Format**: JSON with defined schema (see `RM_5_8_0_GOLDEN_DATASET_SPEC.md`)
- **Immutability**: Golden datasets are version-controlled and immutable once baselined

### 2. Benchmark Metrics Engine
- **Location**: `benchmarks/` (logic only, no runtime)
- **Responsibility**: Compute all defined metrics against golden dataset
- **Independence**: Zero dependency on `core/`, `lts/`, or any runtime module

### 3. Scorecard Generator
- **Output**: Standardized scorecard format (see `RM_5_8_0_SCORECARD.md`)
- **Grades**: A+, A, B, C based on Overall Score thresholds

### 4. Regression Protocol
- **Triggers**: Defined in `RM_5_8_0_EXECUTION_PROTOCOL.md`
- **Baseline**: Stored in `benchmarks/results/baseline/`
- **Decision**: Automated comparison against baseline thresholds

---

## Directory Structure

```
benchmarks/
├── knowledge/
│   ├── character/
│   ├── glossary/
│   ├── scene/
│   ├── narrative/
│   └── style/
├── golden/
│   ├── character/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   ├── glossary/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   ├── scene/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   ├── narrative/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   └── style/
│       ├── easy/
│       ├── medium/
│       └── hard/
├── results/
│   ├── baseline/           # Immutable baseline scores
│   ├── current/            # Latest run results
│   └── history/            # Historical runs for trend analysis
└── .gitkeep
```

---

## Frozen Layer Compliance

The following are **explicitly forbidden** from modification by this framework:

| Layer | Path | Status |
|-------|------|--------|
| Translation Engine | `core/translation_engine/` | FROZEN |
| LTS | `lts/` | FROZEN |
| Knowledge Extraction | `core/knowledge/` | FROZEN |
| Knowledge Validation | `core/knowledge_validation/` | FROZEN |
| Knowledge Review | `core/knowledge_review/` | FROZEN |
| Knowledge Compilation | `core/knowledge_compilation/` | FROZEN |

**Benchmark Framework only reads Knowledge Packages produced by the frozen runtime.** It never invokes, modifies, or depends on runtime internals.

---

## Execution Model

- **Trigger**: Manual or CI/CD (defined in Execution Protocol)
- **Isolation**: Runs in separate process/environment
- **Network**: Zero outbound requests
- **Providers**: Zero provider API calls
- **Output**: Scorecard + Regression Report (Markdown/JSON)

---

## Versioning

- **Benchmark Version**: Tied to RM version (e.g., RM-5.8.0)
- **Golden Dataset Version**: Semantic versioning (v1.0.0, v1.1.0, etc.)
- **Baseline Version**: Immutable once recorded per golden dataset version

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `RM_5_8_0_GOLDEN_DATASET_SPEC.md` | Golden dataset format and structure |
| `RM_5_8_0_METRICS.md` | Metric definitions and computation |
| `RM_5_8_0_SCORECARD.md` | Scorecard format and grading |
| `RM_5_8_0_EXECUTION_PROTOCOL.md` | When and how to run benchmarks |
| `RM_5_8_0_EXECUTION_REPORT.md` | Report template and structure |

---

## Acceptance Criteria for This Document

- [ ] Architecture clearly separates benchmark from runtime
- [ ] Data flow diagram shows no runtime modification
- [ ] Directory structure matches specification
- [ ] Frozen layers explicitly listed and protected
- [ ] No provider/runtime execution in benchmark flow

## Data Flow

```
Novel (Input Text)
       │
       ▼
Knowledge Extraction (Runtime — produces Knowledge Package)
       │
       ▼
Knowledge Package (Structured Output)
       │
       ▼
Golden Dataset Comparison (Benchmark — compares against expected)
       │
       ▼
Benchmark Metrics (Quantitative Scores)
       │
       ▼
Scorecard (Formatted Report with Grades)
       │
       ▼
Regression Decision (Pass/Fail against Baseline)
```