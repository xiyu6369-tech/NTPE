# RM-5.8.6 Runtime Boundary Report

**Version**: RM-5.8.6  
**Date**: 2026-08-05  
**Status**: FROZEN — Boundary Verification Complete

---

## Purpose

Detailed audit of the Benchmark Framework boundary — confirming that:

1. The Benchmark Framework does **NOT** import any Translation Runtime or LTS modules.
2. The Benchmark Framework does **NOT** modify, write to, or alter any Runtime, Translation Package, Knowledge Package, or Provider state.
3. The Benchmark Framework is **fully offline** — zero provider API calls, zero network requests.
4. The only dependency on the Knowledge Layer is via **offline extractor tools** (`tools/knowledge_generation/`), which are stateless and idempotent.
5. The Knowledge Package is **never mutated** by the benchmaright.

---

## 1. Import Audit

### 1.1 Benchmark Imports Knowledge Extractor Tools (Allowed)

```python
# tools/knowledge_benchmark/executor.py:16 — ALLOWED
from tools.knowledge_generation import (
    create_character_extractor,
    create_glossary_extractor,
    create_scene_extractor,
    create_narrative_extractor,
    create_style_extractor,
)
```

**Assessment**: These are stateless factory functions for Knowledge Extractor instances. They are part of the `tools/` layer (build-time), not the Runtime layer. The executor invokes them with `extractor.extract(context)` producing a plain entity list. The Knowledge Package is never written, compiled, or modified by the Benchmark.

### 1.2 Forbidden Imports — ALL ABSENT

| Forbidden Import | Verification Method | Result |
|------------------|---------------------|--------|
| `core.translation_engine` | AST import scan | NOT IMPORTED |
| `core.translation_runtime` | AST import scan | NOT IMPORTED |
| `lts.*` | AST import scan | NOT IMPORTED |
| `core.knowledge_compilation.KnowledgeCompiler` | AST import scan | NOT IMPORTED |
| `core.knowledge_compilation.PackageBuilder` | AST import scan | NOT IMPORTED |
| `core.knowledge.compatibility.provider` | AST import scan | NOT IMPORTED |
| `openai` / `anthropic` / `groq` | AST import scan | NOT IMPORTED |
| `requests` / `urllib` / `http` | AST import scan | NOT IMPORTED |
| `socket` / `aiohttp` / `httpx` | AST import scan | NOT IMPORTED |
| `asyncio` / `ssl` | AST import scan | NOT IMPORTED |

### 1.3 Full Import Scan Results

```text
AST-based import analysis of core/knowledge_benchmark/ and tools/knowledge_benchmark/

scanning... domains checked: provider, network, runtime
Result: PASS — No provider, network, or runtime imports detected

Scoped dependency: tools/knowledge_benchmark/executor.py →
  core/knowledge_generation.models (ExtractionContext) — offline dataclass
  tools/knowledge_generation/*_extractor — offline extractor factories
```

---

## 2. Operation Audit

### 2.1 Verified: Benchmark CANNOT Perform

| Operation | Blocked By | Evidence |
|-----------|------------|----------|
| Import Translation Runtime | No imports to `core.translation_*` or `lts/` | AST scan confirms |
| Call Provider API | No `provider`, `openai`, `anthropic`, `groq` imports | AST scan confirms |
| Make Network Requests | No `requests`, `urllib`, `http`, `aiohttp` imports | AST scan confirms |
| Modify Knowledge Package | Only reads extractor output; never writes packages | Code review |
| Modify Translation Package | Not referencing translation system at all | Import audit |
| Compile Knowledge Package | Does not import `KnowledgeCompiler` | Import audit |
| Write to `artifacts/` | Benchmark writes only to `benchmarks/results/` | File system design |
| Modify Runtime State | No shared mutable state with Runtime | Architecture audit |
| Change Golden Corpus | Golden corpus is read-only (never modified by runner) | Code review |
| Mutate Provider | Provider not imported | Import audit |

### 2.2 Verified: Benchmark CAN Perform (Read-Only Operations)

| Operation | Mechanism | Mutation? |
|-----------|-----------|-----------|
| Read Golden Corpus | `BenchmarkCorpusLoader.load_extractor()` | No |
| Invoke Extractor | `ExtractionExecutor.execute()` — calls `extractor.extract()` | No (extractors are stateless) |
| Compute Metrics | `BenchmarkMetric.compute()` — pure functions | No |
| Generate Scorecard | `BenchmarkScorer.generate_scorecard()` — deduplicated computation | No |
| Run Analysis | `Orchestrator.analyze()` — reads comparisons only | No |
| Generate Dashboard | `DashboardGenerator.build_from_scorecard()` — reads scorecards only | No |
| Write Results | `ReportWriter.write_*()` — writes to `benchmarks/results/` only | Writes own output directory |
| Promote Baseline | `BaselineManager.promote()` — writes to `benchmarks/results/baseline/` only | Writes own output directory |
| Evaluate Regression | `RegressionGate.evaluate()` — pure comparison | No |
| Evaluate Release | `ReleaseGate.evaluate()` — pure decision logic | No |

---

## 3. Network & Provider Isolation

### 3.1 Zero Provider API Calls — Confirmed

The entire `core/knowledge_benchmark/` and `tools/knowledge_benchmark/` codebase contains **zero** references to:
- `openai`
- `anthropic`
- `groq`
- `requests`
- `urllib.request`
- `http.client`
- `socket`
- `asyncio`
- `aiohttp`
- `httpx`
- `ssl`

**All computation is pure Python** — numeric metrics, structural comparisons, JSON I/O.

### 3.2 Executor Extraction Bridge

The `ExtractionExecutor` invokes `tools/knowledge_generation` extractors. These extractors are:

| Extractor Factory | File | Method Called |
|-------------------|------|--------------|
| `create_character_extractor()` | `tools/knowledge_generation/character_extractor.py` | `.extract(context)` |
| `create_glossary_extractor()` | `tools/knowledge_generation/glossary_extractor.py` | `.extract(context)` |
| `create_scene_extractor()` | `tools/knowledge_generation/scene_extractor.py` | `.extract(context)` |
| `create_narrative_extractor()` | `tools/knowledge_generation/narrative_extractor.py` | `.extract(context)` |
| `create_style_extractor()` | `tools/knowledge_generation/style_extractor.py` | `.extract(context)` |

The extractors are:
- **Stateless** — no runtime context is shared
- **Idempotent** — same input produces same output
- **Offline** — no LLM calls, no provider calls, no network
- **Scaffold** — current RM-5.8 extraction uses pattern-based extraction, not LLM

Per `executor.py:97-98`: `"Scaffold extraction - LLM integration pending"`

This is the specified architecture: benchmarks run with scaffold extraction for CI determinism. RM-5.9+ may introduce the LLM path via configuration flags.

---

## 4. Dependency Direction Verification

### 4.1 Permitted Dependency Flow

```
Benchmark Tooling (tools/knowledge_benchmark/)
        │
        ├── imports core/knowledge_benchmark/ (ALLOWED)
        │   ├── models, errors, comparison, scorer, metrics
        │   ├── analysis (orchestrator, failure_classifier, etc.)
        │   ├── dashboard, baseline, regression_gate, release_gate
        │
        └── imports tools/knowledge_generation/ (ALLOWED — offline tool)
            └── character/glossary/scene/narrative/style_extractor

Benchmark Core (core/knowledge_benchmark/)
        │
        ├── self-contained (models, metrics, errors)
        ├── no imports from tools/
        ├── no imports from core.translation_*
        ├── no imports from core.knowledge_compilation
        └── no imports from lts/
```

### 4.2 Verified: NO Reverse Dependencies

| Reverse Path | Checked | Result |
|--------------|---------|--------|
| `knowledge_benchmark` → `translation_engine` | Import scan | NO |
| `knowledge_benchmark` → `knowledge_compilation` | Import scan | NO |
| `knowledge_benchmark` → `lts` | Import scan | NO |
| `knowledge_benchmark` → Non-LTS-production code | Import scan | NO |
| `translation_engine` → `knowledge_benchmark` | Import scan | NO |
| `knowledge_generation` → `knowledge_benchmark` | Import scan | NO |
| `knowledge_compilation` → `knowledge_benchmark` | Import scan | NO |
| `knowledge.comp/compatibility` → `knowledge_benchmark` | Import scan | NO |

---

## 5. Knowledge Package Audit

### 5.1 Packages Never Touched by Benchmark

```python
# benchmark, including NEVER:
#   from core.knowledge_compilation import ...
#   from core.knowledge.compatibility import ...
#   import KnowledgeCompiler, PackageReader, KnowledgePackageProvider, ...
```

**The benchmark reads extractor output directly** — it does NOT use `KnowledgePackageProvider`, `PackageReader`, or `KnowledgeCompiler` to access entities.


### 5.2 Package Invariance

| Path | Read by Benchmark? | Modified by Benchmark? |
|------|-------------------|----------------------|
| `artifacts/knowledge_packages/v1/` | No |
| `artifacts/knowledge_packages/v1/characters.json` | No | No |
| `artifacts/knowledge_packages/v1/glossaries.json` | No | No |
| `artifacts/knowledge_packages/v1/scenes.json` | No | No |
| `artifacts/knowledge_packages/v1/narrative.json` | No | No |
| `artifacts/knowledge_packages/v1/style.json` | nd = no = No |
| `schemas/knowledge/*.json` | No | No |
| `tools/knowledge_generation/*.py` | Read (invoke offline) | No |

---

## 6. Execution Environment Isolation

### 6.1 Command Verification

All benchmark operations are triggered via the CLI only:

```
python -m tools.knowledge_benchmark.cli --all
python -m tools.knowledge_benchmark.cli --dashboard
python -m tools.knowledge_benchmark.cli --promote-baseline
python -m tools.knowledge_benchmark.cli --regression-gate
python -m tools.knowledge_benchmark.cli --release-gate
```

None of these commands involve:
- The Translation Runtime
- The knowledge compilation pipeline
- The knowledge provider pipe
- Any NTP API
- Any LLM provider

### 6.2 Process Isolation

The benchmark runs as a **separate Python process**, not within the Translation Runtime environment:

| Property | Translation Runtime | Benchmark Framework |
|----------|--------------------|-------------------|
| `NTPE_RUNTIME_MODE` | Set/Required | Unset/Not required |
| Loads `core.translation_*` | | No |
| Loads `core.knowledge_compilation` | Via PackageReader | No |
| Makes API calls | Yes (translation) | No |
| Modifies files | Translation output | `benchmarks/results/` only |

---

## 7. Writing Output Constraints

Benchmark writes **only** to `benchmarks/results/` directory tree:

| Path | Purpose | Write-Only? |
|------|---------|-------------|
| `benchmarks/results/current/*_scorecard.json` | Per-extractor scorecards | Write only |
| `benchmarks/results/current/overall_scorecard.json` | Composite scorecard | Write only |
| `benchmarks/results/current/benchmark_report.md` | Human-readable report | Write only |
| `benchmarks/results/current/analysis_report.md` | Analysis output | Write only |
| `benchmarks/results/current/analysis_report.json` | Analysis JSON | Write only |
| `benchmarks/results/current/regression_gate_report.json` | Regression gate report | Write only |
| `benchmarks/results/current/release_gate_result.json` | Release gate result | Write only |
| `benchmarks/results/history/{run_id}/` | Timestamped archives | Write only |
| `benchmarks/results/dashboard/dashboard.md` | Dashboard markdown | Write only |
| `benchmarks/results/dashboard/dashboard.json` | Dashboard JSON | Write only |
| `benchmarks/results/baseline/*` | Promoted baselines and index | Write only |

**Zero writes to `core/`, `lts/`, `artifacts/`, `tools/knowledge_generation/`, or any other directory.**

---

## 8. Summary

| Boundary Aspect | Status | Evidence |
|-----------------|--------|----------|
| Import isolation (from Runtime) | PASS | No `core.translation_*` imports |
| Import isolation (from Compiler) | PASS | No `core.knowledge_compilation` imports |
| Import isolation (from Network) | PASS | No `requests/urllib/http/asyncio` imports |
| Import isolation (from Providers) | PASS | No `openai/anthropic/groq` imports |
| Operation restriction (writes) | PASS | Writes only to `benchmarks/results/` |
| Operation restriction (mutations) | PASS | No Package/Runtime/Provider mutations |
| Dependency direction | PASS | All inbound, no reverse edges |
| Knowledge Package invariance | PASS | Not read, not written |
| Offline execution | PASS | No network, no API calls |
| Extractor bridge | PASS | Invoked as offline tools (factory functions) |

**BENCHMARK BOUNDARY: VERIFIED AND FROZEN**

---

*This boundary is FROZEN as of RM-5.8.6. Any RM-5.9+ changes must preserve these boundaries.*