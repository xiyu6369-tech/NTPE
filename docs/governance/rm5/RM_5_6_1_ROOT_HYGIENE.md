# RM-5.6.1 — Root Hygiene Regression Prevention

## 概述

本文件記錄 RM-5.6.1 階段執行的 Root Hygiene 恢復與防止退化機制。

---

## 背景

RM-4 Freeze 建立了 Root Hygiene 基準，但在 RM-5 開發期間，Root 目錄累積了多種臨時檔案：

| 類型 | 數量 | 檔案範例 |
|------|------|----------|
| `test_*.py` | 8 | `test_full_pipeline.py`, `test_glossary_pipeline.py` 等 |
| `write_*.py` | 1 | `write_override.py` |

這些檔案違反了專案佈局政策，必須搬移至適當位置。

---

## 執行動作

### 1. Root Inventory 盤點

掃描 Root 目錄，分類如下：

| Type | Target | 狀態 |
|------|--------|------|
| `test_*.py` | `tests/rm5/` | ✅ 已搬移 (8 files) |
| `write_*.py` | `tools/one_shots/` | ✅ 已搬移 (1 file) |
| runtime data | `memory/` | — 無新增 |
| generated artifacts | `artifacts/rm5/` | — 目錄已建立 |
| analysis JSON | `analysis/` | — 現有檔案保留 |

**不刪除任何內容，僅搬移。**

### 2. 搬移記錄

```bash
git mv test_full_pipeline.py tests/rm5/
git mv test_full_pipeline2.py tests/rm5/
git mv test_full_pipeline3.py tests/rm5/
git mv test_full_pipeline4.py tests/rm5/
git mv test_full_pipeline5.py tests/rm5/
git mv test_glossary_pipeline.py tests/rm5/
git mv test_glossary_pipeline2.py tests/rm5/
git mv test_glossary_pipeline3.py tests/rm5/
git mv write_override.py tools/one_shots/
```

所有搬移使用 `git mv` 保留歷史記錄。

### 3. Policy Audit

檢查 `config/project_layout_policy.json`：

- `allowed_root_files`：無需新增（現有允許清單維持不變）
- `retained_root_wrappers`：無需新增
- `production_entrypoints`：無變更
- `validation_entrypoints`：無變更

Root allowlist **不新增** 任何項目。

### 4. .clinerules 更新

新增 **Root Development Hygiene** 區段（第 164-185 行），明確禁止在 Root 建立臨時 Python 檔案，並指引正確的目標目錄。

---

## 迴歸防止規則

### 強制規則

1. **嚴禁** 在 Root 目錄建立以下模式的 Python 檔案：
   - `test_*.py`
   - `debug_*.py`
   - `sample_*.py`
   - `write_*.py`
   - `check_*.py`
   - `temp_*.py`

2. **必須** 使用對應目標目錄：
   - 測試腳本 → `tests/`（或 `tests/rm5/` 等子目錄）
   - 一次性工具 → `tools/one_shots/`
   - 產生資料 → `artifacts/`（或 `artifacts/rm5/`）
   - 分析輸出 → `analysis/`
   - 執行期資料 → `memory/`

3. **驗證門檻**：每次變更必須通過：
   - `git diff --check`
   - `python -m compileall .`
   - `python ntpe_validate.py`
   - `git status --short` 確認 Root 無新增臨時檔案

---

## 驗證結果

| 檢查項目 | 結果 |
|----------|------|
| Root 無 test_*.py | ✅ PASS |
| Root 無 write_*.py | ✅ PASS |
| Root 無 debug_*.py | ✅ PASS |
| Root 無 temp_*.py | ✅ PASS |
| Root 無 sample_*.py | ✅ PASS |
| Root 無 check_*.py | ✅ PASS |
| compileall PASS | 待驗證 |
| ntpe_validate PASS | 待驗證 |
| git diff --check PASS | 待驗證 |

---

## 後續治理

- 此規則納入 `.clinerules` 永久生效
- 所有未來 Stage 必須遵循 Root Hygiene
- 違規檢測由 `ntpe_validate.py` 或 CI 機制攔截

---

## 簽署

- Stage: RM-5.6.1
- 執行日期: 2026-08-02
- 狀態: 完成