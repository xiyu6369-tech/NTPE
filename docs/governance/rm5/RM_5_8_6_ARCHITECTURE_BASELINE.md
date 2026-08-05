# RM-5.8 Architecture Baseline

**Version**: RM-5.8 (Frozen LTS Baseline)  
**Date**: 2026-08-05  
**Status**: FROZEN — Reference Architecture for RM-5.9+

---

## Purpose

This document captures the complete RM-5.8 Benchmark Framework architecture as formally accepted in **RM-5.8.6 Benchmark Final Acceptance**. It serves as the immutable reference baseline for all RM-5.9+ development.

**RM-5.9+ Rule**: Only **Extend** — Never **Rewrite** this architecture.

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    BENCHMARK FRAMEWORK (RM-5.8 FROZEN)                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  GOLDEN CORPUS (Immutable Data)                   │   │
│  │  benchmarks/golden/{character,glossary,scene,narrative,style}/    │   │
│  │  {easy,medium,hard}/ — 150 cases total (30 × 5 extractors)       │   │
│  │  benchmarks/spec/benchmark_case_schema.json                       │   │
│  │  benchmarks/spec/benchmark_manifest.json                          │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      BENCHMARK RUNNER                             │   │
│  │  tools/knowledge_benchmark/runner.py  —  Runner class             │   │
│  │  tools/knowledge_benchmark/loader.py  —  BenchmarkCorpusLoader    │   │
│  │  tools/knowledge_benchmark/executor.py — ExtractionExecutor       │   │
│  │  tools/knowledge_benchmark/cli.py     —  CLI entry point          │   │
│  │  tools/knowledge_benchmark/report_writer.py — ReportWriter        │   │
│  │                                                                   │   │
│  │  Pipeline: Load → Execute Extractor → Compare → Score → Report   │   │
│  │  Invokes Knowledge Extractor tools (offline, no LLM)             │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     COMPARISON ENGINE                             │   │
│  │  core/knowledge_benchmark/comparison.py                           │   │
│  │  • EntityMatcher — exact match + semantic equivalence            │   │
│  │  • ExtractionComparison — golden vs predicted pair               │   │
│  │  • ComparisonConfig — matching thresholds                        │   │
│  │  • create_comparison() — produce entity match results            │   │
│  │  • generate_scorecard() — composite scorecard from comparisons    │   │
│  │  • Regression detection: F1/Precision/Recall/Schema drops        │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     METRICS ENGINE                                │   │
│  │  core/knowledge_benchmark/scorer.py — BenchmarkScorer             │   │
│  │  core/knowledge_benchmark/metrics/                                │   │
│  │  ├── accuracy.py     — EntityMatcher, MatchType                  │   │
│  │  ├── precision.py    — PrecisionMetric                           │   │
│  │  ├── recall.py       — RecallMetric                              │   │
│  │  ├── f1_score.py     — F1ScoreMetric                             │   │
│  │  ├── confidence_metrics.py — ConfidenceCalibrationMetric          │   │
│  │  ├── schema_compliance.py — SchemaComplianceMetric                │   │
│  │  └── __init__.py     — BusinessRuleComplianceMetric,              │   │
│  │                         ReviewComplianceMetric                    │   │
│  │                                                                   │   │
│  │  All 12 metrics: Precision, Recall, F1, Missing Rate,            │   │
│  │  Hallucination Rate, Duplicate Rate, Schema Pass Rate,            │   │
│  │  Business Rule Pass Rate, Review Pass Rate, ECE,                  │   │
│  │  False High Confidence, False Low Confidence                     │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     ANALYSIS ENGINE                               │   │
│  │  core/knowledge_benchmark/analysis/                               │   │
│  │  ├── orchestrator.py      — AnalysisOrchestrator, create_analyzer │   │
│  │  ├── failure_classifier.py — FailureClassifier                    │   │
│  │  ├── statistics.py         — StatisticsEngine                     │   │
│  │  ├── trend_analyzer.py     — TrendAnalyzer                        │   │
│  │  ├── suggestion_engine.py  — SuggestionEngine                     │   │
│  │  ├── regression_analyzer.py— RegressionAnalyzer                    │   │
│  │  └── models.py             — AnalysisReport, FailureSummary       │   │
│  │                                                                   │   │
│  │  Output: AnalysisReport (markdown + JSON)                         │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        DASHBOARD                                  │   │
│  │  core/knowledge_benchmark/dashboard.py                            │   │
│  │  • DashboardGenerator — build_from_scorecard()                    │   │
│  │  • DashboardModel — overall_score, overall_grade, extractors      │   │
│  │  • DashboardSlot — per-extractor display slot                     │   │
│  │  • write_dashboard() — outputs dashboard.md + dashboard.json      │   │
│  │                                                                   │   │
│  │  Read-only derivation from scorecards. Regeneratable.             │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│       ┌───────────────────────┼───────────────────────┐                 │
│       ▼                       ▼                       ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   HISTORY    │    │  BASELINE    │    │  REGRESSION  │              │
│  │              │    │   MANAGER    │    │     GATE     │              │
│  │ results/     │    │ baseline/    │    │ regression_  │              │
│  │ history/     │    │ manager.py   │    │ gate.py      │              │
│  │              │    │ models.py    │    │              │              │
│  │ Timestamped  │    │ storage.py   │    │ 8 metric     │              │
│  │ run archives │    │              │    │ thresholds   │              │
│  │              │    │  promote()   │    │ PASS/WARN/   │              │
│  │              │    │  rollback()  │    │ FAIL         │              │
│  │              │    │  list()      │    │ pass_release │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                      │
│         └───────────────────┼───────────────────┘                      │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      RELEASE GATE                                 │   │
│  │  core/knowledge_benchmark/release_gate.py                         │   │
│  │  • ReleaseGate — evaluates scorecard + regression report          │   │
│  │  • ALLOW/BLOCK decision                                           │   │
│  │  • Score ≥ 0.70 requirement                                       │   │
│  │  • Regression must PASS                                           │   │
│  │  • Score drop > 0.02 from baseline = BLOCK                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer Definitions (Frozen)

### 2.1 Golden Corpus — `benchmarks/golden/`

**Purpose**: Immutable ground-truth test data for benchmarking

| Property | Value |
|----------|-------|
| Total Cases | 150 (30 per extractor × 5 extractors) |
| Difficulty Tiers | easy (10), medium (10), hard (10) per extractor |
| Format | JSON per `benchmarks/spec/benchmark_case_schema.json` |
| Immutability | Appended-only; never modified once committed |
| Manifest | `benchmarks/spec/benchmark_manifest.json` — 150 benchmark IDs + SHA-256 checksum |

**Extractors**: character, glossary, scene, narrative, style

---

### 2.2 Runner — `tools/knowledge_benchmark/`

**Purpose**: Orchestrates the full benchmark pipeline

| Component | File | Responsibility |
|-----------|------|---------------|
| Runner | `runner.py` | Load → Execute → Compare → Score → Report |
| Loader | `loader.py` | Read golden corpus from `benchmarks/golden/` |
| Executor | `executor.py` | Invoke Knowledge Extractors against source texts |
| ReportWriter | `report_writer.py` | Write scorecards, overall, report, archive to history |
| CLI | `cli.py` | Command-line entry point with all subcommands |

**Key Classes**:
- `Runner` — main pipeline orchestration
- `BenchmarkCorpusLoader` — reads golden cases and validates schema
- `ExtractionExecutor` — invokes `tools.knowledge_generation.*_extractor` factories
- `ReportWriter` — writes scorecards, overall JSON, markdown report, history archives
- `RunResult` — dataclass holding per-extractor run results

**Constraint**: Only invokes Knowledge Extractor **tools** (offline). Never contacts LLM providers.

---

### 2.3 Comparison Engine — `core/knowledge_benchmark/comparison.py`

**Purpose**: Match extracted entities against golden expected entities

| Class/Object | Purpose |
|-------------|---------|
| `ComparisonEngine` | Main engine: create_comparison(), get_entity_match_results(), generate_scorecard() |
| `ComparisonConfig` | Configuration: entity matcher, regression thresholds |
| `EntityMatcher` | MatchType enum (EXACT, SIMILAR, PARTIAL, NONE) |
| `RegressionType` | Enum: F1_DROP, PRECISION_DROP, RECALL_DROP, etc. |
| `RegressionContext` | Stores baseline → current delta comparisons |
| `RegressionResult` | Per-metric regression detection result |

**Key Method**: `create_comparison(extractor_type, golden_entities, predicted_entities, difficulty_tier, ...) -> ExtractionComparison`

---

### 2.4 Metrics Engine — `core/knowledge_benchmark/metrics/` + `scorer.py`

**Purpose**: Compute all defined metrics from comparisons

| Module | Class/Metric |
|--------|-------------|
| `accuracy.py` | `EntityMatcher`, `MatchType`, `EntityMatchResult` |
| `precision.py` | `PrecisionMetric` — TP/(TP+FP) |
| `recall.py` | `RecallMetric` — TP/(TP+FN) |
| `f1_score.py` | `F1ScoreMetric` — 2·P·R/(P+R) |
| `confidence_metrics.py` | `ConfidenceCalibrationMetric` — ECE + false high/low confidence |
| `schema_compliance.py` | `SchemaComplianceMetric` — schema pass rate |
| `__init__.py` | `BusinessRuleComplianceMetric`, `ReviewComplianceMetric`, `ExactMatchAccuracy`, `FieldLevelAccuracy`, `EntityLevelAccuracy` |
| `scorer.py` | `BenchmarkScorer` — orchestrates all metrics; `ScorerConfig` — difficulty-based targets |

**Aggregation Weight** (Per definition in `RM_5_8_0_METRICS.md`):
```
Extractor_Score = F1 × 0.40 + (1-Missing_Rate) × 0.15 + (1-Hallucination_Rate) × 0.15
                + Schema_Pass_Rate × 0.10 + Business_Rule_Pass_Rate × 0.10
                + (1-ECE) × 0.10
Overall_Score = mean(all Extractor_Scores)
```

---

### 2.5 Analysis Engine — `core/knowledge_benchmark/analysis/`

**Purpose**: Post-benchmark analysis with diagnostic insights

| Module | Class | Responsibility |
|--------|-------|---------------|
| `orchestrator.py` | `Orchestrator`, `create_analyzer()` | Entry point; coordinates all analyses |
| `failure_classifier.py` | `FailureClassifier` | Categorize failures by type, severity |
| `statistics.py` | `StatisticsEngine` | Descriptive statistics on metric distributions |
| `trend_analyzer.py` | `TrendAnalyzer` | Direction analysis (Improving/Stable/Declining) |
| `suggestion_engine.py` | `SuggestionEngine` | Ranked actionable recommendations |
| `regression_analyzer.py` | `RegressionAnalyzer` | Fine-grained regression analysis per extraction |
| `models.py` | `AnalysisReport`, `FailureSummary` | Data models for analysis output |

**Output**: `analysis_report.md` + `analysis_report.json`

---

### 2.6 Dashboard — `core/knowledge_benchmark/dashboard.py`

**Purpose**: Human-readable and machine-readable quality at-a-glance

| Class | Purpose |
|-------|---------|
| `DashboardGenerator` | Builds dashboard from scorecard + regression data |
| `DashboardModel` | Overall score, grade, extractors, regression, trend, suggestions, metadata |
| `DashboardSlot` | Per-extractor: score, grade, precision, recall, f1, ece, missing rate, hallucination rate, schema pass |

**Outputs**:
- `benchmarks/results/dashboard/dashboard.md` — human-readable markdown
- `benchmarks/results/dashboard/dashboard.json` — machine-readable JSON

**Governance**: Dashboard is read-only and regeneratable. Not a source of truth; derived from scorecards.

---

### 2.7 History — `benchmarks/results/history/`

**Purpose**: Timestamped archive of all benchmark runs

| Operation | Method |
|-----------|--------|
| Archive run | `ReportWriter.archive_to_history(run_id)` |
| List history | `ReportWriter.list_history()` |
| Load baseline | `ReportWriter.load_baseline(extractor_name)` |

**Storage Pattern**: `benchmarks/results/history/{benchmark_id}/` contains the full scorecard set.

---

### 2.8 Baseline Manager — `core/knowledge_benchmark/baseline/`

**Purpose**: Immutable baseline storage and promotion lifecycle

| Class | Responsibility |
|-------|---------------|
| `BaselineManager` | promote(), load_baseline(), list_baselines() |
| `BaselineEntry` | Single baseline: run_id, score, grade, metric snapshots |
| `BaselineIndex` | baseline_index.json with active/previous pointers |
| `BaselineStorage` | File I/O for `benchmarks/results/baseline/` |

**Promotion Criteria**:
1. All extractors have executed successfully
2. No extraction errors
3. Overall score ≥ 0.70
4. Regression check against previous baseline passes

**Governance Rules**:
1. Promotion is additive — baselines never deleted
2. Immutable after promotion — data frozen
3. Rollback preserves history — previous accessible
4. Content verifiable (SHA-256)
5. No overwrite — each baseline separate file

---

### 2.9 Regression Gate — `core/knowledge_benchmark/regression_gate.py`

**Purpose**: Ensures no release introduces quality regression beyond tolerance

| Class/Enum | Purpose |
|-----------|---------|
| `RegressionGate` | evaluate(current_scores, baseline_scores) → RegressionGateReport |
| `GateStatus` | PASS, WARNING, FAIL |
| `MetricComparison` | Per-extractor, per-metric delta comparison |
| `GateThreshold` | Warning% + Fail% thresholds per metric (8 metrics) |
| `RegressionGateReport` | Overall status, comparisons, failure/warning count, pass_release |

**Thresholds** (DEFAULT_GATE_THRESHOLDS):

| Metric | Warning Δ | Fail Δ | Inverted? |
|--------|-----------|--------|-----------|
| f1_score | 0.5% drop | 1.0% drop | No |
| precision | 1.0% drop | 2.0% drop | No |
| recall | 1.0% drop | 2.0% drop | No |
| ece | 1.0% rise | 2.0% rise | |
| missing_rate | 1.0% rise | 2.0% rise | |
| hallucination_rate | 1.0% rise | 2.0% rise | |
| schema_pass_rate | 2.0% drop | 5.0% drop | No |
| business_rule_pass_rate | 2.0% drop | 5.0% drop | No |

---

### 2.10 Release Gate — `core/knowledge_benchmark/release_gate.py`

**Purpose**: Final all-or-nothing gate for releasing

| Class | Purpose |
|-------|---------|
| `ReleaseGate` | Evaluates scorecard + regression report → ALLOW/BLOCK |
| `ReleaseDecision` | ALLOW or BLOCK |
| `ReleaseGateResult` | Decision, reason, score details, recommendations |

**Criteria**:
- Regression gate must PASS (FAIL → BLOCK)
- Overall score ≥ 0.70 (below → BLOCK)
- Score drop from baseline > 2 percentage points → BLOCK

---

## 3. Data Flow (Frozen)

### 3.1 Build-Time Flow (Benchmark Run)

```
Golden Corpus (benchmarks/golden/)
       │
       ▼
BenchmarkCorpusLoader.load_extractor(extractor_name)
       │  reads 10 easy + 10 medium + 10 hard cases
       ▼
ExtractionExecutor.execute() per case
       │  invokes tools.knowledge_generation.create_*_extractor()
       │  extractor.extract(ExtractionContext) → entities
       │  OFFLINE — no LLM, no API, no Runtime
       ▼
ComparisonEngine.create_comparison(golden, predicted, difficulty)
       │  EntityMatcher matches golden vs predicted
       │  produces ExtractionComparison
       ▼
BenchmarkScorer.generate_scorecard(comparisons, metadata)
       │  computes all 12 metrics per extractor
       │  aggregation: weighted average → ExtractorScore → OverallScore
       │  produces Scorecard
       ▼
ReportWriter.write_scorecard(name, scorecard) → benchmarks/results/current/{name}_scorecard.json
ReportWriter.write_overall_scorecard(overall) → benchmarks/results/current/overall_scorecard.json
ReportWriter.write_report(markdown) → benchmarks/results/current/benchmark_report.md
ReportWriter.archive_to_history(run_id) → benchmarks/results/history/{run_id}/
```

### 3.2 Analysis Flow (Optional Post-Run)

```
Scorecard (benchmarks/results/current/overall_scorecard.json)
       │
       ▼
Orchestrator.analyze(comparisons, baseline_results)
       │
       ├── FailureClassifier.classify_failures(comparisons)
       ├── StatisticsEngine.compute_distribution(comparisons)
       ├── TrendAnalyzer.analyze_trends(current, history)
       ├── SuggestionEngine.generate_suggestions(analysis)
       └── RegressionAnalyzer.analyze_regression(current, baseline)
       │
       ▼
AnalysisReport.to_markdown() → benchmarks/results/current/analysis_report.md
AnalysisReport.to_json()     → benchmarks/results/current/analysis_report.json
```

### 3.3 Dashboard Generation (Offline)

```
Overall Scorecard → DashboardGenerator.build_from_scorecard(scorecard, regression_check)
       │
       ├── DashboardSlot per extractor (Score, Grade, F1, Precision, Recall, ECE, etc.)
       ├── Trend direction from history
       └── Suggestions from analysis report
       │
       ▼
DashboardGenerator.write_dashboard(dashboard)
       ├── benchmarks/results/dashboard/dashboard.md
       └── benchmarks/results/dashboard/dashboard.json
```

### 3.4 Baseline / Gate Flow (Offline)

```
Current Results → promote() → BaselineIndex (active entry)
       │
       ├── load_baseline() → BaselineEntry.metric_snapshots
       │
       └── RegressionGate.evaluate(current_scores, baseline_scores)
                   │
                   ├── GateStatus.PASS → pass_release = True
                   ├── GateStatus.WARNING → pass_release = True (with caution)
                   └── GateStatus.FAIL → pass_release = False
                            │
                            ▼
                    ReleaseGate.evaluate(current, regression_report, baseline_score)
                            │
                            ├── ALLOW (all checks pass)
                            └── BLOCK (any check fails)
```

---

## 4. Dependency Graph (Verified Acyclic)

```
Golden Corpus (data)
       ↓ read
Runner (tools/knowledge_benchmark/)
       ↓ invoke
Comparison Engine → Metrics Engine → Scorer
       ↓                ↓
       ↓           Scorecard
       ↓                ↓
       └────────────────┬──────────────────┐
                        ↓                  ↓
                   Analysis           Report Writer
                        ↓                  ↓
                   Analysis             History
                   Report
                        ↓
                   Dashboard
                        ↓
                        └──────────────────┐
                                           ↓
                                    Baseline Manager → Baseline Index
                                           ↓
                                    Regression Gate (compare vs baseline)
                                           ↓
                                    Release Gate (consolidated)
```

**Verified**: No cycles. All edges flow in one direction. No module imports a downstream consumer.

---

## 5. Dependency Direction Verification

| Direction | Check | Result |
|-----------|-------|--------|
| Runner → Metrics Engine | runner imports scorer, comparison | PASS |
| Runner → Analysis Engine | CLI imports orchestrator | PASS |
| Runner → Dashboard | CLI imports dashboard_generator | PASS |
| Runner → Regression Gate | CLI imports regression_gate | PASS |
| Runner → Release Gate | CLI imports release_gate | PASS |
| Runner → Baseline Manager | CLI imports baseline_manager | PASS |
| Metrics → Runner | Metrics does NOT import runner | PASS |
| Baseline → Runner | Baseline does NOT import runner | PASS |
| Regression Gate → Runner | Gate does NOT import runner | PASS |
| Release Gate → Runner | Gate does NOT import runner | PASS |
| Engine → Provider | No provider imports at all | PASS |
| Engine → Network | No network imports at all | PASS |
| Engine → Runtime | No runtime imports at all | PASS |

---

## 6. Module Inventory (Complete)

### core/knowledge_benchmark/ (24 Python files)

```
core/knowledge_benchmark/
├── __init__.py          (32 exports, version 5.8.5)
├── models.py            (BenchmarkResult, MetricName, EntityType, DifficultyTier, ...)
├── errors.py            (BenchmarkError, GoldenSampleError, ComparisonError, ...)
├── comparison.py        (ComparisonEngine, ComparisonConfig, RegressionResult, ...)
├── scorer.py            (BenchmarkScorer, ScorerConfig, ...)
├── regression_gate.py   (RegressionGate, GateThreshold, RegressionGateReport, ...)
├── release_gate.py      (ReleaseGate, ReleaseGateResult, ReleaseDecision)
├── dashboard.py         (DashboardGenerator, DashboardSlot, DashboardModel)
├── metrics/
│   ├── __init__.py      (BusinessRuleComplianceMetric, ReviewComplianceMetric, ...)
│   ├── accuracy.py      (EntityMatcher, MatchType)
│   ├── precision.py     (PrecisionMetric)
│   ├── recall.py        (RecallMetric)
│   ├── f1_score.py      (F1ScoreMetric)
│   ├── confidence.py  (ConfidenceCalibrationMetric)
│   └── schema_compliance.py (SchemaComplianceMetric)
├── analysis/
│   ├── __init__.py
│   ├── orchestrator.py  (Orchestrator, create_analyzer)
│   ├── failure_classifier.py
│   ├── statistics.py
│   ├── trend_analyzer.py
│   ├── suggestion_engine.py
│   ├── regression_analyzer.py
│   └── models.py
└── baseline/
    ├── __init__.py
    ├── manager.py       (BaselineManager, create_baseline_manager)
    ├── models.py        (BaselineEntry, BaselineIndex)
    └── storage.py       (BaselineStorage)
```

### tools/knowledge_benchmark/ (5 Python files)

```
tools/knowledge_benchmark/
├── __init__.py
├── runner.py            (Runner, RunResult)
├── loader.py            (BenchmarkCorpusLoader)
├── executor.py           (ExtractionExecutor, ExecutionResult)
├── cli.py               (CLI entry point)
└── report_writer.py     (ReportWriter)
```

### benchmarks/ (Data directories)

```
benchmarks/
├── golden/              (150 JSON case files)
│   ├── character/{easy,medium,hard}/ (10 each)
│   ├── glossary/{easy,medium,hard}/  (10 each)
│   ├── scene/{easy,medium,hard}/     (10 each)
│   ├── narrative/{easy,medium,hard}/ (10 each)
│   └── style/{easy,medium,hard}/     (10 each)
├── spec/
│   ├── benchmark_case_schema.json
│   ├── benchmark_manifest.json
│   └── difficulty_definition.md
├── results/
│   ├── baseline/  (.gitkeep)
│   ├── current/   (latest run scorecards)
│   ├── history/   (timestamped archives)
│   └── dashboard/ (dashboard outputs)
└── knowledge/     (placeholder .gitkeep files)
```

---

## 7. Version Pinning

| Artifact | Version | Location |
|----------|---------|----------|
| Benchmark Framework | `5.8.5` | `core/knowledge_benchmark/__init__.py.__version__` |
| Golden Dataset | `v1.0.0` | `benchmarks/spec/benchmark_manifest.json` |
| Case Schema | `1.0.0` | `benchmarks/spec/benchmark_case_schema.json` |
| CLI | `RM-5.8.5` | `tools/knowledge_benchmark/cli.py` |
| Scorecard | `RM-5.8.5` | `core/knowledge_benchmark/scorer.py` |
| Regression Gate | `RM-5.8.5` | `core/knowledge_benchmark/regression_gate.py` |
| Release Gate | `RM-5.8.5` | `core/knowledge_benchmark/release_gate.py` |
| Dashboard | `RM-5.8.5` | `core/knowledge_benchmark/dashboard.py` |
| Baseline | `RM-5.8.5` | `core/knowledge_benchmark/baseline/*.py` |

---

## 8. RM-5.9+ Extension Guidelines

| Extension Type | Guideline | Example |
|----------------|-----------|---------|
| New metric | Add class to `metrics/`; register in `ScorerConfig` | `PolarityMetric` |
| New analysis module | Add to `analysis/`; wire into `Orchestrator` | `SemanticAmbiguityAnalyzer` |
| Updated dashboard section | Add to `DashboardModel` fields | `extractor_load_time` |
| New extractor type | Requires RFC; version bump | `magic_system` extractor |
| Improved golden corpus | Append new cases; update manifest | v1.1.0 corpus |
| CI/CD integration | `ci/benchmark.yml` as GitHub Actions workflow | Smoke + full benchmark on PR |
| Scaffold elimination | Replace `ExtractionExecutor` with real LLM-backed extraction | NTP API calls |
| New regression rule | Add to `GateThreshold.supported_metrics` | Per-extractor auditing |

**Never**:
- Modify `ComparisonEngine` method signatures
- Modify `ExtractorScore` calculation formula
- Remove any public API from `__init__.py`
- Change difficulty tier definitions (EASY/MEDIUM/HARD)
- Allow benchmark to import `core.translation_*` or `lts/`
- Call provider APIs from benchmark processes

---

## 9. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_8_6_FINAL_ACCEPTANCE.md` | Formal acceptance record |
| `RM_5_8_6_RUNTIME_BOUNDARY_REPORT.md` | Runtime boundary audit detail |
| `RM_5_8_6_ACCEPTANCE_CHECKLIST.md` | Checklist used for verification |
| `RM_5_8_6_EXECUTION_REPORT.md` | Validation execution evidence |
| `RM_5_8_0_BENCHMARK_ARCHITECTURE.md` | Original architecture baseline |
| `RM_5_8_0_METRICS.md` | Metric definitions and formulas |
| `RM_5_8_0_SCORECARD.md` | Scorecard format and grading |
| `RM_5_8_1_CORPUS_DESIGN.md` | Corpus design and coverage |
| `RM_5_8_5_BASELINE_POLICY.md` | Baseline lifecycle |
| `RM_5_8_5_REGRESSION_POLICY.md` | Regression gate thresholds |
| `RM_5_8_5_DASHBOARD_SPEC.md` | Dashboard spec |

---

*This architecture is FROZEN as of RM-5.8.6 (2026-08-05). All RM-5.9+ development must Extend Only.*