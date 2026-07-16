# TIC Batch 7 — Offline Translation Quality Gate Integration

## 用途與狀態

本批將 TIC Batch 6.1 的兩筆人工批准 Active Regression 整合為純離線、固定案例、fail-closed 的品質 Gate。它可評估歷史譯文、人工候選譯文、Prompt Candidate 離線輸出、人工修訂草稿與 regression fixture；只有至少一筆 regression 明確適用且全部通過時，才允許標記為 `quality_candidate`、`review_ready` 與 `regression_safe`。

## Applicability 限制

Subject-reference-shift 只在固定韓文 source、source SHA 與可選 case metadata 一致時適用。Lexical-choice 除固定 source 與 SHA 外，還要求明確 regression ID，或完整的 case ID、failure case ID 與 alignment ID；因此不會把所有 `인간` 建立成全域規則，也不會只因譯文出現「鄭泰義」或「明白」而套用 subject regression。

沒有固定案例可明確套用時，結果是 `not_applicable`，且不允許 quality candidate；`not_applicable` 絕不等於 PASS。空文字、非法型別、未知 regression、遭篡改 SHA、缺失 approval 或 evaluator context 錯誤都會 fail closed，成為 `invalid_input` 或 `insufficient_evidence`。

## Blocking 語意

`defect_blocking` 保存 Failure Corpus 的原始 defect metadata；兩筆案例目前皆為 `false`。`regression_gate_blocking` 表示固定 regression 失敗時是否阻止 quality candidate，兩筆皆為 `true`。兩者用途不同，Batch 6.1 Artifact 未被改寫。

## Production 邊界

Gate 不連接 Runtime、Provider、Prompt、QA Engine 或 Production translation path，不執行 Provider、不產生新譯文、不自動批准候選，也不寫入磁碟完成評估。Microbenchmark 只衡量離線記憶體內評估。

本批尚未改善 Production 翻譯，也未驗證任何新 Provider 譯文；只提供兩個固定歷史案例的離線 regression gate。TIC Batch 8 尚未開始。
