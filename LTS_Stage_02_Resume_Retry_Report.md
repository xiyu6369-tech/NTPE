# NTPE 1.1 LTS Stage-02 Resume / Retry 強化 Report

## Status
ALL PASS

## Scope
本 Stage 在 Stage-01 TXT 翻譯入口上增量新增 Resume / Retry 強化。

## Implemented
- chunk-level resume state：`output/<input_stem>_resume_state.json`
- 已完成 chunk reuse：比對 `source_hash` 與 chunk 輸出檔
- Provider retry：支援 503、429、ResourceExhausted、timeout、暫時服務不可用
- Exponential backoff：`--max-retries`、`--retry-base-seconds`
- Launcher dry-run retry option validation

## Compatibility
- 保留 `python ntpe_translate_txt.py input.txt output` 用法
- 不改 NTPE 1.0 Stable Frozen 層
- 不破壞 Foundation / CLI / SDK / Integration / Workflow / Runtime API / External API / Web UI

## Tests
`PYTHONPATH=. pytest -q tests/lts_stage_01 tests/lts_stage_02 tests/stable_release_preparation tests/stable_release_finalization tests/stable_release_completion`

Result: `19 passed`
