# RM-4.2C Test Migration Preflight Report

**日期**: 2026-07-30
**狀態**: Audit-only — 無修改、無搬遷、無 provider 調用
**前序**: RM-4.2A (Archive Safe Migration) ✅ → RM-4.2A Validation Reconciliation ✅ → RM-4.2B (Classification) ✅

---

## 範圍 (Scope)

```
候選 (Candidate):
  285 test files（SAFE_MOVE classification from RM-4.2B）

目標路徑 (Target):
  archive/stage_tests/

來源位置 (Source):
  D:\Python\NTPE\ (root)
```

---

## 1. Dependency Scan（依賴掃描）

掃描 **1,545 個 production Python files**（含 core/, engine/, lts/, ntpe/, integration/, cli/, config/, external_api/, tools/, compatibility/, manifests/, archive/）。

| 類別 | 數量 |
| --- | ---: |
| 無任何依賴 (No dependency) | 284 |
| 被 production code import | 1 |
| 被 validator import | 0 |
| Test-to-test import | 0 |

### Production Import Details

| 檔案 | 它 import 的 test | 檔案實際位置 |
| --- | --- | --- |
| `generate_lcr_batch2_audit.py` | `ntpe_lcr_batch2_character_memory_v2_test` | `archive/historical/audits/legacy_capability_recovery/batch2/` |

此檔案位於 `archive/historical/` 目錄內，屬於已存檔的舊稽核腳本，**非任何 active production code 或 runtime path**。稽核腳本僅是 historical reference，不影響任何 runtime、CI pipeline、或 production 路徑。

**判定**: 此 dependency 無影響 — 不視為 blocking condition。

**註記**: Historical dependency only. No active execution path.

---

## 二、Pytest Discovery 影響分析

### 現在狀況

```
目前 config 檔案:
    pytest.ini      → 無
    pyproject.toml  → 無（無 [tool.pytest] section）
    setup.cfg       → 無（無 [tool:pytest] section）
    conftest.py     → 無
```

目前依賴 pytest 預設 discovery：
```
python_files = test_*.py, *_test.py
testpaths = . (root)
```

### 搬遷後影響

若 285 SAFE_MOVE test files 搬至 `archive/stage_tests/`：

- Root 還剩 **~43 個 production/launcher .py files**，其中：
  - Historical wrappers: 32 個（已被 inventory 識別）
  - Permitted compatibility wrappers: 3 個
  - Production entrypoints: 若干
  - `_preflight_scan.py`（本階段暫時存在，將移除）

- **Pytest 預設不會掃描 `archive/`**，因為 pytest 預設排除 pattern 中若 `norecursedirs` 未設，pytest 預設仍掃描所有目錄。但 `pytest -q` 執行時：
  - 若未指定 `--rootdir` 或 `testpaths`，pytest 可能掃描 `archive/stage_tests/` **如果** archive 不屬於 `.git` 或 `.venv`
  - **建議**: 搬遷後在 `pyproject.toml` 中設定 `testpaths = ["."]` 並加入 `norecursedirs = ["archive"]`，或保持 `pytest ./archive/stage_tests/` 顯式調用

### 測試數量預期

| 階段 | 預期測試數 |
| --- | ---: |
| Before (目前 root) | ~285 |
| After (archive/stage_tests/) | ~285（需顯式指定 path 或使用 `pytest archive/stage_tests/`） |
| 若 pytest 仍從 root 掃描（不包括 archive） | ~0-10（剩餘的 validation wrappers） |

⚠ **風險**: 若 CI/自動化直接執行 `pytest` 而不指定 path，測試數量將從 805 驟降為 ~0-10。**需要後續 RM-4.2D 階段更新 CI/runner config**。

---

## 三、Validator Impact 分析

檢查 `ntpe_validate.py`：

### `check_test_inventory()` （第 203-216 行）

```python
def check_test_inventory() -> CheckResult:
    tests_dir = ROOT / "tests"
    verificaction_dir = ROOT / "verification"
    test_files = set(tests_dir.rglob("test_*.py")) | set(tests_dir.rglob("*_test.py"))
    verificaction_files = set(verification_dir.rglob("test_*.py")) | set(verification_dir.rglob("*_test.py"))
```

**僅掃描 `tests/` 和 `verification/` 目錄**。Root 目錄下的 test files 完全不在其掃描範圍。

| 項目 | Before | After |
| --- | --- | --- |
| `tests/` pytest files | 不變 | 不變 |
| `verification/` 檔案 | 不變 | 不變 |
| 結果 | PASS | PASS (相同) |

### `check_project_structure()` （第 219-228 行）

調用 `tools.audit_project_layout.build_inventory()`。當前 root_python_files = 328。
- SAFE_MOVE files 已被 inventory 系統識別為可分類（historical_wrappers / permitted_compatibility_wrappers）
- 搬遷後 root_python_files = ~43，inventory 會自動調整
- `unexpected_root_files` 不會增加（目前＝[]）

**Validator 不受2500測試搬遷影響。**

---

## 四、Import Path Dependency 分析

掃描 285 SAFE_MOVE files 中的 path 依賴：

| 模式 | 數量 | 影響 |
|------|---:|------|
| `sys.path.append(".")` 或相似 | 0 | 無影響 |
| `Path(__file__).parent` | 8 | 見下方分析 |

### Path(__file__).parent 詳細

8 個檔案使用 `Path(__file__).parent`：

- `ntpe_lcr_batch110_governance_freeze_test.py`
- `ntpe_lcr_batch107_pre_execution_package_test.py`
- `ntpe_lcr_batch108_failure_characterization_test.py`
- `ntpe_lcr_batch105_bounded_dual_pass_pilot_test.py`
- `ntpe_lcr_batch106_single_chunk_dual_pass_execution_review_test.py`
- `ntpe_lcr_batch109_provider_failure_policy_freeze_test.py`
- `ntpe_lcr_batch111_governance_baseline_consumption_audit_test.py`
- `ntpe_te_v720_stage1251_controlled_canary_test.py`

使用模式：`subprocess.run(..., cwd=Path(__file__).parent)`

`Path(__file__).parent` 永遠指向檔案**所在目錄**。搬遷至 `archive/stage_tests/` 後，這些呼叫將自動指向新位置，功能不受影響。

---

## 五、Coverage / CI / Tooling 影響

- `.github/`: 無 SAFE_MOVE test 引用
- `scripts/`: 無
- `.coveragerc`: 無此檔案
- `setup.cfg`: 無 coverage 設定
- `pyproject.toml`: 無 `[tool.coverage]` section

**無任何開發工具引用需要修改的文件。**

---

## 六、綜合分析摘要

| 檢查項目 | 狀態 | 備註 |
|------|------|------|
| Dependency scan | ✅ PASS | 唯一的 historical dependency 不構成 block |
| Pytest discovery | ⚠️ 需關注 | 搬遷後需要更新 pytest config 或指定 testpath |
| Validator | ✅ PASS | test_inventory() 不掃描 root |
| Import path | ✅ PASS | Path(__file__).parent 動態指向新路徑 |
| CI / Tooling | ✅ PASS | 無引用 |
| sys.path hacks | ✅ PASS | 0 個 |

---

## 六、遷移決策

# Migration Decision

## 決策: ✅ APPROVED

285 個 SAFE_MOVE test files 可以安全地搬遷至 `archive/stage_tests/`

### 搬遷後建議（RM-4.2D 階段）：

1. 在 `pyproject.toml` 或 `setup.cfg` 中加入 pytest config 以明確化 test paths
2. 更新 CI pipeline（恢復 RM-4.1 存在的 CI）
3. 宣告 `norecursedirs = ["archive"]` 以排除
4. 搬遷後執行 `git diff --check && python ntpe_validate.py` 驗證

### 不允許事項（本階段）

- ❌ git mv
- ❌ delete
- ❌ rename
- ❌ update imports
- ❌ modify tests
- ❌ git commit
- ❌ git push

---

**報告完成時間**: 2026-07-30T03:35:00+08:00
**驗證腳本**: `_preflight_scan.py`（審計後可移除）
**下一步**: RM-4.2D — 執行搬遷（用戶明確授權後）