# NTPE Repository Status Report — Read-Only Analysis

Generated: 2026-07-27T11:37:00+08:00
Agent: AI assistant using Copilot CLI runtime in VS Code

---

# 1 Executive Summary

目前倉儲有明確且可復現的治理基線：一組以 `launcher_translate.py -> ntpe_production_translate.py -> TranslationRuntime` 為生產主幹的生產脊線已存在；同時保留大量歷史 wrapper、凍結測試與重複工具。最大且最直接的技術債為被保留的全工作樹 ZIP（NTPE.zip），以及重複/平行工具與測試導致的維護成本。此報告整理已發現的治理文件、完成項與尚未完成的整併計畫，並給出後續建議（僅建議，不新增政策）。

---

# 2 Governance History

找到的重要治理文件與用途（摘要）：

- Architecture Consolidation Audit
  - [NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md)
  - 用途：完整架構稽核，識別 KEEP/MERGE/DELETE/ARCHIVE 類別、重複能力、測試鏡像與風險評估。屬於審核結論與建議，不直接修改程式。
  - 是否完成：Audit 已完成（報告已生成，無更改）。

- Project Layout Consolidation (Stage 0)
  - [NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md)
  - 用途：低風險根目錄整理策略（Stage 0），保留歷史 Root Wrappers、移動非 Python 歷史檔到 verification/，產出保留清單供後續清理。
  - 是否完成：Stage 0 已執行（報告有 Outcome 與統計），但有 commit/push hold 策略（不在此任務中提交任何變更）。
  - 相關產物：[artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json)

- Consolidation Batch Plan
  - [CONSOLIDATION_BATCH_PLAN.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json)
  - 用途：分批（Batch 1..5）列出 Repository Hygiene、Test Consolidation、Shared Utilities、Quality API Consolidation、Production Path Simplification 等批次計畫與風險、測試/回退策略。
  - 是否完成：Plan 文件存在，為 roadmap；多數批次屬建議／待執行。

- Legacy Capability Recovery (LCR) Audit
  - [LCR_BATCH1_AUDIT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/legacy_capability_recovery/batch1/LCR_BATCH1_AUDIT.md)
  - 用途：列出 legacy 能力、風險（例如 credential 暴露）與設計建議。
  - 是否完成：Audit（設計/稽核）已完成；後續修正屬實作範疇。

- Project Layout policy and supporting docs
  - [PROJECT_LAYOUT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/docs/PROJECT_LAYOUT.md)
  - [config/project_layout_policy.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/config/project_layout_policy.json)
  - 用途：描述 Stage 0 原則、目錄定位與 artifacts/manifests/verification 的定位與處理。
  - 是否完成：文件存在並被 Stage 0 參照。

其他相關稽核/證據文件（摘要與位置）
- [REPOSITORY_SIZE_REPORT.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json)
- [REPOSITORY_DUPLICATES.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/REPOSITORY_DUPLICATES.json)
- KEEP/DELETE/MERGE 清單與 batch 實作資料（位於 audits/architecture_consolidation）

---

# 3 Repository Baseline

基於審核與 Stage 0 文件，將目前 repository 的資源定位（僅整理既有說明）：

- Production
  - 定位：以 `launcher_translate.py -> ntpe_production_translate.py -> TranslationRuntime` 為生產脊線。
  - 證據：見 Architecture Audit 中的生產路徑說明與 `PRODUCTION_PATH.json` 提及（[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md)）。

- Validation
  - 定位：tests/、artifacts/、manifests/ 與 verification/ 承接驗證（Stage 0 保留 freeze 與歷史測試以便回退/審核）。
  - 證據：[REPOSITORY_SIZE_REPORT.json] 與 [PROJECT_LAYOUT.md]（驗收與 tests/ 說明）。

- Legacy
  - 定位：大量歷史 Root Wrappers、Stage 特定包、NTPE.zip（全工作樹備份）等被標記為 ARCHIVE 或 DELETE_CANDIDATES，但以 audit/manifest 方式保留。
  - 證據：[DELETE_CANDIDATES.json], [KEEP.json], [NTPE.zip 在 REPOSITORY_SIZE_REPORT.json 列示]。

- Evidence & Artifacts
  - 定位：`artifacts/` 保存階段產物（例如 MOVE_MAP.json）、`manifests/` 保存凍結哈希與驗收邊界。
  - 證據：`artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json`、多個 manifests 檔案在 manifests/。

- Tools
  - 定位：`tools/` 下包含 audit 與 layout 檢查工具（例如 `tools/audit_project_layout.py`）。
  - 證據：倉內 `tools/` 與 `compatibility/`、`core/*/audit.py` 等檔案。

---

# 4 Existing Governance Rules

（僅整理既有內容，不新增）

從現有文件整理出可觀察到的治理規則類別與要點：

- Root Policy / Root Layout rules
  - 來源文件：[PROJECT_LAYOUT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/docs/PROJECT_LAYOUT.md)、[config/project_layout_policy.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/config/project_layout_policy.json)
  - 要點：Stage 0 採「低風險整理」，保留歷史 Root Wrappers 與非 Python 歷史檔至 `verification/`；使用 `ntpe_validate.py` 驗證 root allowlist。

- Artifact Policy
  - 來源文件：[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md] 中的 Artifact retention 節與 [REPOSITORY_SIZE_REPORT.json]
  - 要點：歷史/Provider 證據應保留且外部化，Provider 原始回應不得直接寫入 Audit ZIP；要使用 SHA-256 與 manifest 保全。

- Validation Policy
  - 來源文件：Architecture Audit 與多個 batch 數據（batch reports）
  - 要點：任何合併或刪除動作需伴隨回退與相容性 wrapper；測試去重需以 pytest collection parity 與保留兼容 wrapper 為前提。

- Legacy / Archive Policy
  - 來源文件：CONSOLIDATION_BATCH_PLAN.json 與 LCR_BATCH1_AUDIT.md
  - 要點：Legacy 能力與實驗性 candidate 應先 archive 並保留證據，必須有 rollback manifest 才能刪除。

注意：以上均為現有文件顯示的規則/政策摘要 — 未新增或變更任何策略。

---

# 5 Current Compliance

概括：倉庫在許多規則上是「部分符合」或「審核合格但未執行整併」。具體項目：

- 符合（evidence）
  - Production boundary 明確並被保留：論據見 [NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md] 中的生產路徑說明與 KEEP 列表（證據：AST/引用檢查）。
  - Stage 0 root-layout 原則已被執行（低風險搬移、verification/ 建構、RETAINED_ROOT_WRAPPERS 產生）：見 [NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md] 與 artifacts MOVE_MAP.json。
  - Artifact 保留原則被文件化（保留 manifests 與證據外部化策略）：見 [REPOSITORY_SIZE_REPORT.json] 的 Artifact retention 片段。

- 偏離（evidence）
  - 大量重複實作與測試鏡像尚未被合併（Architecture Audit 列出大量 duplicate/serialization/hash 邏輯），證據：[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md], [REPOSITORY_DUPLICATES.json]。
  - 極高體積技術債（NTPE.zip 佔 587.8MB）尚未外部化或移除（Plan 建議但未執行）：證據 [REPOSITORY_SIZE_REPORT.json]。
  - Stage 11 / Stage 12 的離線/實驗性 artefacts 與 frozen manifests 仍保留，可能造成維護負擔（Architecture Audit 建議 preserve+compatibility wrappers）。
  - LCR 批次發現的憑證暴露（在審核 copy 中被紅acted）指出存在未解決的安全後續工作（見 [LCR_BATCH1_AUDIT.md]）。

對每一偏離項的直接證據已在上列文件中連結。

---

# 6 Technical Debt (仍存在且需未來處理，僅列未解決項)

- NTPE.zip（全工作樹 ZIP）被保留於 repository，佔用 587,775,785 bytes，是最大且最直接的儲存負擔；建議外部化（archive）或移出至外部儲存。證據：[REPOSITORY_SIZE_REPORT.json]。

- 重複實作（SHA-256、canonical JSON、序列化、boundary flags、frozen dataclasses 等）在多個檔案中重複，增加合併風險與測試負擔。證據：[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md], [REPOSITORY_DUPLICATES.json]。

- 測試鏡像與重複 root/integration tests（約 8 個 root/integration 完全相同），需要 Test Consolidation 但尚未執行。證據：[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md]（Tests 段落）與 batch2 report。

- 冷凍 Stage wrappers 與兼容 import 導致代碼重複與 API 混淆（Adaptive Context / Stage 11）；合併風險高，需要兼容 façade 策略。證據：[NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md]、KEEP.json 條目。

- LCR 發現的 credential 暴露（已在稽核時紅acted）指出需要憑證輪替與安全審計修補（尚未在倉內看到修補提交）。證據：[LCR_BATCH1_AUDIT.md]。

---

# 7 Remaining Work (未完成項目，按優先度分類，根據 CONSOLIDATION_BATCH_PLAN.json 與 audit 建議整理)

High Priority
- Externalize or remove NTPE.zip（Batch 1 Repository Hygiene） — 風險/回退：archive+SHA-256 manifest（必要）。
  - 參考：[CONSOLIDATION_BATCH_PLAN.json]、[REPOSITORY_SIZE_REPORT.json]

- Protect production boundaries during any runtime/quality consolidation（Batch 5 風險 CRITICAL）— 確保 timeout/retry/resume 不被破壞。
  - 參考：Architecture Audit (Highest risks 段)

- Address credential exposure from legacy sources (LCR Batch1 finding) — 憑證輪替與審計。
  - 參考：[LCR_BATCH1_AUDIT.md]

Medium Priority
- Test Consolidation: 去重 exact duplicates 並保留 compatibility wrappers（Batch 2）。
  - 參考：[CONSOLIDATION_BATCH_PLAN.json], batch2 test reports。

- Shared Utilities consolidation (primitive-by-primitive，避免 big-bang)（Batch 3）。

Low Priority
- Quality API Consolidation（Batch 4）：分階段整併 Stage 11 進入 quality/assessment 等，需大量人為驗證。

已完成或部分完成（非再做）
- Stage 0 Project Layout Consolidation（低風險 root 整理）已執行並產出 MOVE_MAP 與 retained lists，但不在版本庫中提交變更（HOLD）。
  - 參考：[NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md], artifacts MOVE_MAP

---

# 8 Recommendations (僅建議，不能建立新 Policy)

- 立刻（短期）執行 Batch 1 的「外部化 NTPE.zip」工作，但採嚴格的 inventory → archive → manifest → 回退練習，並在 archive 前建立 SHA-256 與 restore 清單（Architecture Audit 已建議）。

- 在任何 Shared Utilities 或 Production Path 的修改前，先建立兼容 façade 與回退演練（小步驟、primitive-by-primitive，不做 big-bang）。

- 進行一輪憑證掃描與安全修補（針對 LCR 提及的 credential 暴露），並記錄在同一 decision register 的後續行動欄。

- 將 Test Consolidation 作為中短期項目（先做 collection parity 與保留 compatibility wrappers，再逐步合併）。

- 任務分配建議：高優先度（externalize ZIP, credentials, production-boundary safety）— 由架構/安全小組共同負責；中優先度（測試、shared utils）— 由工程團隊循 batch 計畫執行。

---

# Decision Register（決策登錄）

| 決策 | 來源文件 | 狀態 | 是否仍有效 |
|------|----------|------|------------|
| Root Python 不應持續膨脹（Stage 0 採低風險整理，Root Wrappers 保留，後續獨立 cleanup） | [NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md) | 已採用（Stage 0 已執行） | 是 |
| Historical Artifacts 不可覆寫；使用 SHA-256 與 manifests 外部化 | [NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md) | 已採用（建議） | 是 |
| 減少重複工具（canonical JSON, SHA, serialization）需逐步 primitive-by-primitive 進行 | [CONSOLIDATION_BATCH_PLAN.json](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json) | 建議中 | 是（需小步驟執行） |
| Stage 12 A/B expansion 應停止並移至 experiments | [NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md](D:/Python/NTPE.worktrees/repository-governance-recovery-analysis/audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md) | 已建議 | 是 |

---

# Validation / Completion Report

- 本次分析共檢索並檢視治理相關檔案匹配數量（符合搜尋模式的文件總數）：148 檔（包含 audits/, artifacts/, docs/ 與 filename pattern matches）。
- 找到的 Governance 文件：148（同上匹配計數，含 audit reports、batch plans、keep/delete/merge 清單、manifests、stage 報告）。
- 找到的 Consolidation 專案（Batch 計畫）：5（見 CONSOLIDATION_BATCH_PLAN.json 中列出的 5 個批次）。
- 已完成事項（或已執行但未 commit）：Stage 0 Project Layout Consolidation（低風險根目錄整理，產出 MOVE_MAP 與 retained lists）；LCR Batch1 audit 已完成（設計/稽核）。
- 未完成事項（主要）：Batch 1..5 中除 Stage 0 外的多數批次尚未執行（externalize ZIP、test consolidation、shared utilities 合併、quality API consolidation、production path simplification）。

Repository Compliance Summary（簡述）
- 生產邊界與主要 runtime 被保留並文件化：合規。
- 多數整併建議與刪除候選仍為「計畫/建議」，尚未執行：偏離治理基線（因尚未落地）。

---

# Evidence index (主要檔案)

- audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md
- audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json
- audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json
- audits/architecture_consolidation/REPOSITORY_DUPLICATES.json
- audits/architecture_consolidation/KEEP.json
- audits/architecture_consolidation/DELETE_CANDIDATES.json
- audits/legacy_capability_recovery/batch1/LCR_BATCH1_AUDIT.md
- docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md
- docs/PROJECT_LAYOUT.md
- artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json
- config/project_layout_policy.json

（倉內還有其他稽核與 batch report JSON/MD 檔，請參見 audits/ 與 docs/ 子目錄以取得完整清單。）

---

# Notes & Constraints

- 本任務為 Read-Only Analysis：未對任何原始碼或內容執行 rename/move/delete/modify。僅新增本報告檔案。
- 不含 commit / push。請維持此工作流程原則。

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

