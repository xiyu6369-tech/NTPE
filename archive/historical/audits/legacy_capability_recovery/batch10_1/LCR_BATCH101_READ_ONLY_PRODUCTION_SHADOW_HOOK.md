# LCR Batch 10.1 — Read-only Production Shadow Hook

Status: **PASS**

本批在 `core/adaptive_context_runtime_shadow/hook.py` 的 prompt package 建立完成後、Provider request 建立前，加入唯一的 `after_chunk_package_prepared` guarded metadata-only hook。Production 修改僅為 import 與 try/except hook call；預設 `LCR_SHADOW_ENABLED=false`、`LCR_KILL_SWITCH=true`。

Hook 僅計算 Chunk Cache identity、Multilingual Profile identity 與 prepare-only Provider Routing evidence。Character/Context 不注入、cache hit 不套用、dual-pass 不執行、Semantic Verification 不成為正式 gate。Prompt、Provider identity、Resume 與 Output contract 前後 hash 均一致；Provider requests=0、network requests=0。

真實 `sleep(0.2)` 與 Event 阻塞測試證明 caller 在 20 ms wait budget 後返回 `timed_out`；單一 daemon worker、最多一個 in-flight、零等待 backlog，busy call 直接 degraded。逾時結果即使稍後完成也會丟棄，且不寫 evidence sink。

Exception、timeout 與 evidence sink failure 全部隔離；Production baseline 繼續。Rollback 可透過 kill switch、global flag，或 revert 單一 hook-call commit，無資料 migration。`ready_for_extended_shadow` 不代表 active integration；下一步需另行人工批准。
