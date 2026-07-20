# NTPE Project Layout

一般翻譯請從根目錄執行 `launcher_translate.py`；正式產品翻譯入口為 `ntpe_production_translate.py`。專案健康檢查使用 `ntpe_validate.py`。

Stage 0 採低風險整理：既有歷史 Root Wrappers 暫時保留在根目錄，不做搬移、去重或測試入口整併。完整清單記錄於 `artifacts/ntpe_v20_stage0_project_layout_consolidation/RETAINED_ROOT_WRAPPERS.json`，供後續獨立 cleanup stage 評估。

`verification/` 保存 Stage 0 新增的結構驗收入口，以及已安全收納的非 Python 歷史說明、changelog、instruction 與 patch。`tests/` 則保存可由 pytest 收集的單元、整合、效能與回歸測試。

- `artifacts/`：各階段產生的離線證據與驗證報告。
- `manifests/`：凍結版本、檔案雜湊與驗收邊界紀錄。
- `docs/`：使用、架構與發佈說明。
- `tools/`：離線維護、產物生成與稽核工具。
- `core/`、`lts/`：翻譯與產品執行程式碼。
- `config/`：專案設定與結構政策。

一般使用者不需要進入 `verification/`、`artifacts/`、`manifests/`、`audits/` 或 `tests/`。`python tools/audit_project_layout.py` 會檢查目前核准的 root allowlist，避免新增未分類檔案。
