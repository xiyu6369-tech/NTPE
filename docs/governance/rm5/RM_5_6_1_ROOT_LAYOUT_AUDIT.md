# RM-5.6.1 — Root Layout Audit

## Root 目錄佈局審計報告

### 審計時間
2026-08-02

### 審計範圍
`D:\Python\NTPE` 根目錄所有檔案與目錄

---

## 1. Root 檔案完整清單（搬移後）

### 允許的 Root 檔案（依 `config/project_layout_policy.json`）

| 類別 | 檔案數 | 狀態 |
|------|--------|------|
| 專案配置 | `.clineignore`, `.clinerules`, `.editorconfig`, `.gitattributes`, `.gitignore` | ✅ |
| 文檔 | `README.md`, `VERSION.txt` | ✅ |
| 覆蓋配置 | `character_database_override.json`, `character_override.json`, `glossary_override.json` | ✅ |
| 生產入口點 | `launcher_translate.py`, `ntpe_production_translate.py` | ✅ |
| 驗證入口點 | `ntpe_validate.py` | ✅ |
| 相容包裝器 | `launcher.py`, `ntpe_translate_batch.py`, `ntpe_translate_txt.py`, `ntpe_provider_setup.py`, `ntpe_provider_verify.py`, `ntpe_provider_audit.py`, `ntpe_provider_benchmark_session.py` | ✅ |
| 保留包裝器 | `create_context_pipeline_integration.py`, `create_context_prompt_integration.py`, `create_voice_batch1.py`, `ntpe_batch_monitor.py`, `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py` | ✅ |
| 其他允許 | `requirements.txt`, `original_ko_chunk_000001.json` | ✅ |

**總計：~32 個允許檔案**

---

### Root 目錄結構（允許的目錄）

| 目錄 | 狀態 |
|------|------|
| `.ai/`, `.agents/`, `.codex/`, `.kilo/`, `.vscode/` | ✅ 配置目錄 |
| `.git/`, `.gitignore` 相關 | ✅ 版控 |
| `.ntpe_runtime_checkpoints/`, `.ntpe_test_sandbox/`, `.pytest_cache/` | ✅ 執行期 |
| `analysis/`, `archive/`, `artifacts/`, `backup/` | ✅ 資料目錄 |
| `benchmark/`, `cache/`, `cli/`, `compatibility/` | ✅ |
| `config/`, `core/`, `docs/`, `engine/` | ✅ 核心原始碼 |
| `external_api/`, `failed_chunks/`, `final_output/` | ✅ |
| `input/`, `integration/`, `logs/`, `lts/` | ✅ |
| `manifests/`, `memory/`, `ntpe/`, `output/` | ✅ |
| `packaging/`, `performance/`, `platform_services/` | ✅ |
| `profiles/`, `prompt_packages/`, `regression/` | ✅ |
| `release_candidate/`, `runtime_api/`, `schemas/` | ✅ |
| `scripts/`, `sdk/`, `stable_release/` | ✅ |
| `tests/`, `tmp/`, `tools/` | ✅ |
| `translated/`, `translation/`, `ui/` | ✅ |
| `verification/`, `web_ui/`, `workflow/` | ✅ |
| `context/` | ✅ 新增 |

**總計：~40+ 個允許目錄**

---

## 2. 違規檢測結果（搬移前 vs 後）

| 違規類型 | 搬移前 | 搬移後 | 狀態 |
|----------|--------|--------|------|
| `test_*.py` | 8 個 | 0 個 | ✅ 修正 |
| `write_*.py` | 1 個 | 0 個 | ✅ 修正 |
| `debug_*.py` | 0 個 | 0 個 | ✅ 合規 |
| `sample_*.py` | 0 個 | 0 個 | ✅ 合規 |
| `check_*.py` | 0 個 | 0 個 | ✅ 合規 |
| `temp_*.py` | 0 個 | 0 個 | ✅ 合規 |

---

## 3. 目標目錄驗證

### tests/rm5/（新建）
- test_full_pipeline.py
- test_full_pipeline2.py
- test_full_pipeline3.py
- test_full_pipeline4.py
- test_full_pipeline5.py
- test_glossary_pipeline.py
- test_glossary_pipeline2.py
- test_glossary_pipeline3.py
**共 8 檔案** ✅

### tools/one_shots/（既有）
- write_override.py（新增）
- 既有 17 檔案
**共 18 檔案** ✅

### artifacts/rm5/（新建）
- 目錄已建立，待未來產生物放置 ✅

### analysis/（既有）
- 既有 6 個 glossary JSON 檔案
- 無新增 ✅

### memory/（既有）
- 既有 7 個檔案
- 無新增 ✅

---

## 4. Policy 合規性檢查

### config/project_layout_policy.json 關鍵欄位

```json
{
  "allowed_root_files": [...],  // 32 項，無需變更
  "allowed_root_directories": [...],  // 40+ 項，含 tests, tools, artifacts, analysis, memory
  "production_entrypoints": ["launcher_translate.py", "ntpe_production_translate.py"],
  "validation_entrypoints": ["ntpe_validate.py"],
  "permitted_compatibility_wrappers": [...],  // 7 項
  "retained_root_wrappers": [...],  // 6 項
  "ignored_root_directories": ["__pycache__"]
}
```

**結論**：Policy 文件無需更新，現有規則已涵蓋所有目標目錄。

---

## 5. RM-4 Freeze 基準對比

| 指標 | RM-4 Freeze | RM-5 開發期 | RM-5.6.1 修正後 |
|------|-------------|-------------|-----------------|
| Root Python 檔案數 | ~32 | ~41 (+9) | ~32 |
| Root test_*.py | 0 | 8 | 0 |
| Root write_*.py | 0 | 1 | 0 |
| Root 臨時檔案 | 0 | 9 | 0 |

**Root Python 數量已恢復至 RM-4 Freeze 水準** ✅

---

## 6. 簽署

- 審計人員：自動化治理流程
- 審計日期：2026-08-02
- 狀態：**通過** — Root 佈局符合 Policy，無違規殘留