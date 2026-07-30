# LCR Batch 10.3 — Extended Read-only Shadow — Context／Scene Memory

Status: **PASS**

本批只在既有 `after_chunk_package_prepared` 單一 bounded worker 中加入 Context／Scene eligibility、selection、scope validation、fingerprint、token estimate 與 cache impact planning。`LCR_CONTEXT_SCENE_SHADOW` 預設關閉，kill switch 預設開啟。

Snapshot 在 caller thread 建立，為 defensive、detached、redacted immutable view；worker 不持有原 Context Store、Character Store 或 production package。Selection 僅使用 Batch 3 公開 validate/select API；expired、stale、conflict、AI inference 與 out-of-scope records 均不選入，unresolved reference 保持 unresolved。

Context 與 previous translation 均未注入 Prompt；scene state、cache identity 均未套用；Prompt、Provider、Resume、Output 與兩個 Store 不變。Provider requests=0、network requests=0。單一 worker、單一 in-flight、零 backlog；逾時結果丟棄且 late evidence writes=0。Activation gate 最多為 `ready_for_dual_pass_shadow`，不授權 Dual-pass、Semantic Verification 或 Active Integration。
