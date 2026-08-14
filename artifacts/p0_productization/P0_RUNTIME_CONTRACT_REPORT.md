# P0 Runtime Contract Report

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## 5.1 Production Entry Chain

### Verified Chain

```
launcher_translate.py (8 lines)
    �� imports
ntpe_production_translate.py (main entry)
    �� instantiates
TranslationRuntime (core/translation_runtime/runtime.py)
    �� delegates to
lts/txt_translation_runtime.py (translate_txt function)
```

### launcher_translate.py

- **Lines**: 8
- **Role**: Trivial wrapper/delegator
- **Action**: `from ntpe_production_translate import main` → `raise SystemExit(main())`
- **No logic** — pure delegation

### ntpe_production_translate.py

- **Lines**: ~2560
- **Role**: Official Production CLI Entry
- **Commands**: `txt`, `batch`, `regression`, `evaluate`, `corpus`, `doctor`
- **Key Features**:
  - Pipeline mode switch: `--pipeline` (runtime/legacy), default via `NTPE_RUNTIME_PIPELINE` env var
  - Speed profiles: fast, balanced, quality
  - Quality profiles: fast, balanced, novel, literary, quality, premium
  - Retry/QA/timeout configuration
  - RM-8.3/8.4 feature flags: `--quality-delivery-v83`, `--quality-delivery-formats-v83`
  - TE v7 (ACE) validation flags for canary/shadow/policy/rollout
  - Creates `TranslationRuntime(root=ROOT)` for each translation
  - Builds `TxtTranslationOptions` or `BatchTranslationOptions`
  - Calls `runtime.translate_txt(options)` or `runtime.translate_batch(options)`

### TranslationRuntime (core/translation_runtime/runtime.py)

- **Lines**: 254
- **Version**: "1.2-professional-stage-14.2"
- **Role**: Formal Translation Runtime Facade
- **Key Methods**:
  - `translate_txt(options)` → delegates to `lts.txt_translation_runtime.translate_txt(options, root=self.root)`
  - `translate_batch(options)` → delegates to `lts.batch_translation_runtime.translate_batch(options, root=self.root)`
  - `main_txt(argv)`, `main_batch(argv)` — direct LTS entrypoints
  - Provider management: `bind_ai_provider_manager`, `register_ai_provider`, `complete_provider_prompt`, `stream_provider_prompt`
  - Session/Pipeline/Resource/Plugin management
  - Checkpoint/recovery: `checkpoint`, `checkpoint_error`, `checkpoint_completed`, `recovery_summary`
  - `describe()` — returns formal runtime contract
  - `validate_compatibility()` — backward compatibility verification

### lts/txt_translation_runtime.py

- **Lines**: 2562
- **Role**: LTS TXT Translation Runtime (frozen baseline)
- **Key Function**: `translate_txt(options: TxtTranslationOptions, root) -> dict`
- **Pipeline Modes** (via `NTPE_RUNTIME_PIPELINE` env var):
  - **runtime** (default): Uses `RuntimeOrchestrator` for RM-6.4.2+ pipeline
  - **legacy**: Uses original LTS translation loop with QA/discipline/retry

---

## 5.2 TranslationRuntime Contract

### translate_txt() Signature

```python
def translate_txt(self, options: Any) -> dict[str, Any]:
    from lts.txt_translation_runtime import translate_txt
    return translate_txt(options, root=self.root)
```

### TxtTranslationOptions (dataclass, frozen=True)

Key fields:
- `input_path: Path` — input TXT file
- `output_dir: Path` — output directory
- `chunk_size: int = 1000` — chunk size (min 300)
- `model: str = "meta/llama-3.3-70b-instruct"` — NVIDIA model ID
- `resume: bool = True` — enable chunk resume
- `dry_run: bool = False` — build packages only
- `max_retries: int = 3` — provider retry count
- `provider_attempts: int | None` — total provider attempts (overrides speed profile)
- `retry_base_seconds: float = 5.0` — exponential backoff base
- `glossary_path: Path | None` — custom glossary
- `character_memory_path: Path | None` — character memory JSON
- `qa_enabled: bool = True` — enable QA checks
- `qa_fail_policy: str = "retry"` — retry|fail|warn
- `min_length_ratio: float = 0.18` — minimum translation length ratio
- `max_korean_chars: int = 2` — max Korean chars in output
- `max_repeated_lines: int = 2` — max repeated lines
- `quality_profile: str = "novel"` — quality profile
- `speed: str = "balanced"` — speed profile
- `quality_integration_v72: bool = False` — TE v7.2 integration
- `quality_context_scene_v72: bool = False` — RM-8.2 cross-chunk context
- `quality_delivery_v83: bool = False` — RM-8.3 delivery pipeline
- `quality_delivery_formats_v83: tuple[str, ...] = ("txt",)` — output formats

### Chunk Execution

1. **Text splitting**: `split_text(text, chunk_size)` — paragraph-aware, min 300 chars
2. **Resume check**: Compares `source_hash` (SHA256[:16]) with resume state
3. **Prompt package**: `build_prompt_package()` — builds full provider package
3. **Provider call**: `translate_package_with_retry()` — with fallback models, timeout handling
4. **Post-processing**: Locked dictionary, formatter, naturalness, collocation, voice register
5. **QA**: Quality V5 + Legacy QA + Discipline runtime integration
6. **Retry logic**: Adaptive feedback, segment recovery, targeted retry
7. **Resume state**: Updated after each chunk (status, source_hash, output_path, qa)

### Retry & Timeout

- **Provider retry**: `provider_attempts` (default: max_retries + 1)
- **Model fallback**: `NTPE_FALLBACK_MODELS` env var / `--fallback-models`
- **Exponential backoff**: `retry_delay_seconds(attempt, base_seconds)` = base * 2^(attempt-1)
- **Timeout retry delays**: `NTPE_TIMEOUT_RETRY_DELAYS` (default: 5,15,30)
- **Capacity retry delays**: `NTPE_CAPACITY_RETRY_DELAYS` (default: 60,120,180)
- **Fast-fail**: `NTPE_SHORT_CHUNK_TIMEOUT_FAST_FAIL=1` for short chunks

### Resume

- **State file**: `{output_dir}/{input_stem}_resume_state.json`
- **Format**: Versioned JSON with `chunks` dict keyed by zero-padded chunk index
- **Skip condition**: `resume=True` AND `status in {"success","pass_with_warning"}` AND `source_hash matches` AND output file exists
- **Live progress**: `{output_dir}/{input_stem}_live_progress.json` — real-time status

### Provider Invocation Boundary

- **Engine**: `TranslationEngine(root=root_path)` 
- **Method**: `engine.translate_package(package, package_path)`
- **Package**: Dict with `model_profile`, `prompt`, `source`, `knowledge`, `runtime`, `metadata`
- **Response**: Dict with `status`, `translation`, `output_path`, `error`, `attempt`, `provider_model`, `provider_elapsed_seconds`

---

## 5.3 LTS Resume SoT

### *_resume_state.json

```json
{
  "version": "1.1-lts-stage-05",
  "chunks": {
    "000001": {
      "status": "success",
      "source_hash": "a46b49d8a2999809",
      "output_path": "...",
      "updated_at": "2026-08-07T00:41:11"
    }
  },
  "events": [],
  "input": "...",
  "output_dir": "...",
  "chunk_total": 3,
  "updated_at": "..."
}
```

### *_live_progress.json

```json
{
  "status": "running|success|failed",
  "input": "...",
  "output_dir": "...",
  "chunk_total": 3,
  "chunk_completed": 2,
  "current_chunk": 3,
  "current_step": "provider_and_qa_attempt_1|runtime_execute|finalizing",
  "updated_at": "..."
}
```

### Verified Behaviors

| Aspect | Behavior |
|--------|----------|
| Identity | Per-chunk `source_hash` (SHA256[:16] of chunk text) |
| Skip completed | Yes — exact hash match + file exists + non-empty |
| Failed chunks | Retried on resume (status not in success set) |
| Duplicate provider request | **NO** — completed chunks skipped by hash verification |
| Retry on resume | Failed/qa_failed chunks retried from provider |
| Dry-run | Status = "dry_run", no provider call, state saved |

---

## DRIFT_FOUND: None

All runtime contracts verified against actual implementation. No drift detected between specification expectations and runtime behavior.