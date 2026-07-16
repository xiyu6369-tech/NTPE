# TIC Batch 6.1 — Human Approval and Regression Activation

## 狀態

TIC Batch 6.1 已將 Batch 6 的兩筆 correction draft 依使用者明確指示，逐字升格為 `human_approved`，並為相同的兩個固定歷史案例建立 active regression protection。這不是 Production 修正，也不是通用語意引擎。

## 人工批准文字與 provenance

`subject_reference_shift` 批准譯文：

> 被拋在遠方的那個男人雖然像個怪物，但至少他仍然是個理智清醒的人，他也會明白這種情況不可能是鄭泰義故意製造的。

`lexical_choice` 批准譯文：

> 相當理性的人

兩筆記錄皆為 `approval_status = human_approved`、`reviewer_type = human`、`human_provenance = explicit_user_approval`。Batch 6 draft 文字沒有被進一步潤飾或改寫；Lexical 案例只將固定案例中的「人間」改為「人」，沒有建立 `인간 → 人` 全域替換。

## Active regression

Subject-shift 固定案例會拒絕歷史錯誤譯文，因為它把「明白此情況」的認知主體錯置為鄭泰義。批准譯文通過，因為前述遠方男人仍是認知主體，而鄭泰義保留在「不可能故意製造此情況」的否定施事關係中。

Lexical-choice 固定案例會拒絕「相當理性的人間」，因為 `人間` 是此案例的 forbidden phrase。批准譯文「相當理性的人」符合此案例的 `human_person` allowlist。兩個 evaluator 都會拒絕無關譯文；其能力只涵蓋這兩個 frozen cases，不代表能偵測所有主語錯置或詞彙錯誤。

## 邊界

Batch 6 Root Cause 維持 `evidence_supported`，未升格為 `human_confirmed`。本批沒有修改或接入 Runtime、Provider、Prompt、QA Engine、Glossary、Stage 11、Stage 12 或 Production translation path；沒有執行 Provider、網路請求或重新翻譯。

因此，本批只允許宣稱「2 個固定歷史品質案例已建立 active regression protection」。它尚未證明整體翻譯品質改善，也沒有套用 Production fix。TIC Batch 7 尚未開始。
