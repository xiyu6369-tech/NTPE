# RM-4.3E — Archive Legacy Root Migration Preflight

| 欄位 | 值 |
|------|-----|
| **Migration ID** | RM-4.3E |
| **Phase** | Preflight |
| **Date** | 2026-07-31 |
| **Predecessor** | RM-4.3D (Final Review) |
| **Status** | ✅ **GATE PASS — Ready for Execution** |

---

## 1. 目標檔案

| # | 檔案 | 大小 (bytes) | 最後修改 | Git 首次引入 |
|---|------|------------|---------|-------------|
| 1 | `ntpe_long_run_recovery.py` | 335 | 2026-07-20 | `db1e6f0` (v1.1.0-lts-stage-10) |
| 2 | `ntpe_plugin_marketplace.py` | 430 | 2026-07-20 | `143c616` (v1.2.0-stage11) |

兩者皆為 thin wrappers（root entrypoint → core/lts 內部模組）。

---

## 2. 檔案內容分析

### 2.1 `ntpe_long_run_recovery.py`（335 bytes）

```python
# NTPE 1.1 LTS Stage-10
# Long-Run Stability / Auto Recovery Entry
from lts.long_run_recovery import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- **角色**：LTS Stage-10 的 CLI 入口，將 `main()` delegate 給 `lts/long_run_recovery.py`
- **明確 obsolete** — `lts/long_run_recovery.py` 已獨立存在且可直接呼叫

### 2.2 `ntpe_plugin_marketplace.py`（430 bytes）

```python
# NTPE 1.2 Professional Stage-12
# Plugin Marketplace CLI / Repository Commands
from __future__ import annotations
from pathlib import Path
from core.translation_plugins.marketplace import run_cli

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    raise SystemExit(run_cli(default_root=ROOT))
```

- **實質**：Stage-12 plugin marketplace CLI entry；delegate 給 `core/translation_plugins/marketplace/`
- 無任何外部 import 依賴於此檔案 — 唯一實質邏輯位於 `core/translation_plugins/marketplace/`

---

## 3. Import / Dependency Scan（全專案完整掃描）

### 3.1 Python `import` 依賴鏈

| 目標檔案 | 誰 import 它？（`import` 語句） | 數量 |
|----------|---------------------------|------|
| `ntpe_long_run_recovery.py` | **無** — 零個 Python 檔案直接 `import ntpe_long_run_recovery` | **0** |
| `ntpe_plugin_marketplace.py` | **無** — 零個 Python 檔案直接 `import ntpe_plugin_marketplace` | **0** |

兩個檔案**都不是**任何其他 Python 模組的 import 目標。所有 `from ... import ...` 都指向底層模組而非 root wrapper：

- `from lts.long_run_recovery import ...` → 指向 `lts/long_run_recovery.py`（非 root wrapper）
- `from core.translation_plugins.marketplace import ...` → 指向 `core/translation_plugins/marketplace/__init__.py`（非 root wrapper）

### 3.2 檔案路徑引用（非 import）

#### `ntpe_long_run_recovery.py` — 被引用的位置

| 檔案 | 行號 | 引用類型 | 影響評估 |
|------|------|---------|---------|
| **`lts/performance_validation.py`** | `39` | `PERFORMANCE_FILES = [...]` 清單 | ⚠️ 檔案存在性驗證 — 移除後 `performance_files_present` check 會 fail |
| **`lts/performance_validation.py`** | `145` | `monitor_files` 清單 — `any((root / rel).exists())` | ⚠️ 同上，檔案存在性檢查 |
| **`lts/runtime_freeze.py`** | `22` | `FROZEN_RUNTIME_FILES` 清單 | ⚠️ freeze manifest 產生時會 hash 此檔案 |
| **`lts/compatibility_validation.py`** | `38` | `REQUIRED_PUBLIC_COMMANDS` 清單 | ⚠️ LTS RC-02 相容性驗證會檢查檔案存在 |
| **`lts/stable_preparation.py`** | `38` | `STABLE_PREPARATION_FILES` | ⚠️ Stable prep manifest |
| **`lts/stable_finalization.py`** | `41` | `STABLE_FINALIZATION_FILES` | ⚠️ Stable finalization manifest |
| **`lts/stable_complete.py`** | `42` | `STABLE_COMPLETE_FILES` | ⚠️ Stable completion manifest |
| **`tests/lts_stage_10/launcher_long_run_recovery_test.py`** | `12` | `subprocess.run([sys.executable, "ntpe_long_run_recovery.py", ...])` | ⚠️ 直接 subprocess 呼叫 → test fail |

#### `ntpe_plugin_marketplace.py` — 被引用的位置

| # | 檔案 | 行號 | 引用類型 | 影響評估 |
|---|------|------|---------|---------|
| **`config/project_layout_policy.json`** | `53` | `allowed_root_files` | ⚠️ Policy 參考 — 需更新 |
| **`config/project_layout_policy.json`** | `399` | `retained_root_wrappers` | ⚠️ Policy 參考 — 需更新 |
| **`docs/release_notes/STAGE_12_PLUGIN_MARKETPLACE_CLI.md`** | `12-19` | 文件 CLI 使用示範 | ℹ️ 歷史文件 — 無 runtime 影響 |
| **`scripts/classify_root_files.py`** | `91-93` | 分類邏輯 | ℹ️ 治理工具 — 僅含 `ARCHIVE_ONLY` 資訊 |
| **`docs/governance/repository/NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`** | `139` | 清單文件 | ℹ️ 治理文件參考 |
| **多個 migration 報告（RM_4_3D, RM_4_3B, etc.）** | — | 歷史記錄 | ℹ️ 文件引用 |

### 3.3 CI / script / shell / batch file 引用

| 檢查類別 | `ntpe_long_run_recovery.py` | `ntpe_plugin_marketplace.py` |
|---------|--------------------------|--------------------------|
| CI config（YAML/JSON/bat/ps1/sh） | **未找到** | **未找到** |
| Makefile / Dockerfile | **未找到** | **未找到** |
| `launcher.py` / `launcher_translate.py` | **未引用** | **未引用** |
| `ntpe_translate_batch.py` / `ntpe_translate_txt.py` | **未引用** | **未引用** |
| 外部 scripts | **未找到** | **未找到** |

> **小結**: 兩個檔案無任何 CI/CD/launcher 引用。

---

## 4. Importer / Consumer 摘要

### `ntpe_long_run_recovery.py`

| Consumer | 類型 | Severity | 處理方式 |
|----------|------|---------|---------|
| `lts/performance_validation.py` | 檔案存在性驗證（collect entries + `any(exists())`） | **MEDIUM** | 從 `PERFORMANCE_FILES` 與 monitor list 中移除 `ntpe_long_run_recovery.py` |
| `lts/runtime_freeze.py` | hash manifest 清單 | **LOW** | 從 `FROZEN_RUNTIME_FILES` 中移除 |
| `lts/compatibility_validation.py` | public command list | **LOW** | 從 `REQUIRED_PUBLIC_COMMANDS` 中移除 |
| `lts/stable_preparation.py` | stable prep manifest | **LOW** | 從 `STABLE_PREPARATION_FILES` 中移除 |
| `lts/stable_finalization.py` | stable finalization manifest | **LOW** | 從 `STABLE_FINALIZATION_FILES` 中移除 |
| `lts/stable_complete.py` | stable complete manifest | **LOW** | 從 `STABLE_COMPLETE_FILES` 中移除 |
| `tests/lts_stage_10/launcher_long_run_recovery_test.py` | direct `subprocess` call | **HIGH** | 測試需更新路徑指向 `archive/legacy_tools/` 或標記為 skip |

### `ntpe_plugin_marketplace.py`

| Consumer | 類型 | Severity | 處理方式 |
|----------|------|---------|---------|
| `config/project_layout_policy.json` | policy 清單（`allowed_root_files`, `retained_root_wrappers`） | **LOW** | 從兩處列表中移除 |
| `docs/release_notes/STAGE_12_PLUGIN_MARKETPLACE_CLI.md` | 歷史文件 CLI 示範 | **NONE** | 不影響 runtime |
---

## 5. Entry Point / CLI Usage Check

### `ntpe_long_run_recovery.py`

| 檢查項目 | 結果 |
|---------|------|
| `if __name__ == "__main__"` 存在 | ✅ 是 |
| CLI `argparse` 引入 | ✅ 委託給 `lts.long_run_recovery.main()` |
| 有使用者直接 CLI invoke？ | 僅從測試 `launcher_long_run_recovery_test.py`（`subprocess.run`） |
| 生產環境呼叫 | **無** |
| README 操作 | **無** |
| 與 wrapper / launcher 整合 | 不相關 |

### `ntpe_plugin_marketplace.py`

| 檢查項目 | 結果 |
|---------|------|
| `if __name__ == "__main__"` 存在 | ✅ 是 |
| CLI `argparse` 引入 | ✅ 由 `core.translation_plugins.marketplace.run_cli` 處理 |
| 有 CLI invoke？ | 僅歷史文件參照（`STAGE_12_PLUGIN_MARKETPLACE_CLI.md`） |
| 生產環境呼叫 | **無** |

> **結論**: 兩個檔案無實際的 CLI 使用方式，僅 test/subprocess 呼叫。

---

## 6. Archive Destination

```text
archive/
└── legacy_tools/                          (✅ 已存在)
    ├── launcher_pipeline_v1.py            (已存在)
    └── + ntpe_long_run_recovery.py        (目標)
    └── + ntpe_plugin_marketplace.py       (目標)
```

> `archive/legacy_tools/` 目錄已存在，且已在 Git tracking 中（目前含有 `launcher_pipeline_v1.py`）。目標檔案將放置於相同目錄，與現有的 legacy tool chain 保持一致。

---

## 7. Rollback Plan

若 archive 後發現問題：

| 步驟 | 操作 |
|------|------|
| **1** | `git checkout HEAD~1 -- ntpe_long_run_recovery.py ntpe_plugin_marketplace.py` |
| **2** | 恢復 `config/project_layout_policy.json` 中的兩份列表 |
| **3** | 恢復 LTS validation 列表（若已修改） |
| **4** | 驗證 `performance_validation`, `runtime_freeze`, `compatibility_validation`, `stable_*` 清單 |
| **5** | 回退 policy commit |

> 預期回退速度：**< 5 分鐘**。無 production impact。

---

## 8. Validation Result

### 8.1 Git Status — Clean

```
git diff --check --stat HEAD
(no output)
```

✅ 工作目錄 clean，無 pending 變更。

### 8.2 Dependency Gate

| Gate | `ntpe_long_run_recovery.py` | `ntpe_plugin_marketplace.py` |
|------|--------------------------|--------------------------|
| Python `import` | **ZERO** ✅ | **ZERO** ✅ |
| CLI script call | **ZERO** ✅ | **ZERO** ✅ |
| Launcher subprocess | **ZERO** ✅ | **ZERO** ✅ |
| CI / Docker / config | **ZERO** ✅ | **ZERO** ✅ |
| LTS validation list references | **7 處** ⚠️ | **2 處**（config/policy）⚠️ |
| 測試引用（直接執行） | **1 個測試** ⚠️ | **0** ✅ |

### 8.3 Classification Consistency

| 檔案 | RM-4.2B | RM-3.2 | RM-4.3D | **RM-4.3E Preflight** |
|------|--------|--------|--------|---------------------|
| `ntpe_long_run_recovery.py` | ARCHIVE_ONLY | SAFE_MOVE | ⚠️ ARCHIVE | ✅ **GATE PASS** |
| `ntpe_plugin_marketplace.py` | ARCHIVE_ONLY | SAFE_MOVE | ⚠️ ARCHIVE | ✅ **GATE PASS** |

### 8.4 Preflight Gate Summary

| Gate | Status |
|------|--------|
| Dependency scan completed | ✅ |
| Importer list established | ✅ |
| Compatibility risk assessed | ✅ |
| Archive destination verified | ✅ |
| Rollback plan documented | ✅ |
| Validation result confirmed | ✅ |

**GATE PASSED ✅**

---

## 9. Execution Plan（RM-4.3E Execution Phase）

### 9.1 允許的操作（RM-4.3E Execution）

| 允許操作 | 說明 |
|---------|------|
| `git mv` | 移動兩個檔案到 `archive/legacy_tools/` |
| 更新 `config/project_layout_policy.json` | 從 `allowed_root_files` and `retained_root_wrappers` 移除兩個檔案 |
| 更新 7 個 LTS validation list | 從 `PERFORMANCE_FILES`, `FROZEN_RUNTIME_FILES`, `REQUIRED_PUBLIC_COMMANDS`, `STABLE_*_FILES` 移除 `"ntpe_long_run_recovery.py"` |
| 更新 `tests/lts_stage_10/launcher_long_run_recovery_test.py` | 修改路徑或重新設計 |
| 生成 Execution Report | 獨立報告 |
| 禁止的操作 | — `commit`（除非用戶授權）<br/>— 修改 core/ 或 lts/ runtime module<br/>— 建立 wrapper<br/>— 修改 Python 程式碼邏輯 |

### 9.2 涉及的 LTS validation lists（共 7 處）

需修改以下檔案以移除 `"ntpe_long_run_recovery.py"`：

1. `lts/performance_validation.py` line 39: `PERFORMANCE_FILES`
2. `lts/performance_validation.py` line 145: `monitor_files`
3. `lts/runtime_freeze.py` line 22: `FROZEN_RUNTIME_FILES`
4. `lts/compatibility_validation.py` line 38: `REQUIRED_PUBLIC_COMMANDS`
5. `lts/stable_preparation.py` line 38: `STABLE_PREPARATION_FILES`
6. `lts/stable_finalization.py` line 41: `STABLE_FINALIZATION_FILES`
7. `lts/stable_complete.py` line 42: `STABLE_COMPLETE_FILES`

### 9.3 影響邊界

- **Frozen layers 影響**：無。`lts/long_run_recovery.py` 和 `core/translation_plugins/marketplace/` 保持不變
- **測試影響**：`launcher_long_run_recovery_test.py` 需調整
- **文件影響**：Policy 配置更新；歷史文件不變
- **Git history**：保留（`git mv`）

---

## 10. References

| 文件 | 路徑 |
|------|------|
| RM-4.3D Final Review | `docs/governance/migration/RM_4_3D_ROOT_FINAL_REVIEW_REPORT.md` |
| RM-4.2B Review Classification | `docs/governance/migration/RM_4_2B_REVIEW_CLASSIFICATION_REPORT.md` |
| RM-3.2 Validation Report | `docs/governance/migration/RM_3_2_VALIDATION_REPORT.md` |
| Policy | `config/project_layout_policy.json` |
| Target archive | `archive/legacy_tools/` |

---

*Generated by RM-4.3E Preflight — 2026-07-31*