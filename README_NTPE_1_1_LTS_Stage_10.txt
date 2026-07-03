NTPE 1.1 LTS Stage-10: Long-Run Stability / Auto Recovery
==========================================================

新增入口：

    python ntpe_long_run_recovery.py output

批次翻譯可選擇啟用長跑 heartbeat：

    python ntpe_translate_batch.py input output --continue-on-failure --heartbeat --auto-recovery

常用參數：

    --heartbeat
        啟用 Batch_Heartbeat.json。

    --heartbeat-seconds 60
        保留於 metadata 中，用於長時間執行監控。

    --stale-after-seconds 1800
        判斷 resume/heartbeat 是否過久未更新。

    --auto-recovery
        在 batch report 中標記長跑自動恢復 metadata。

    python ntpe_long_run_recovery.py output --stale-after-seconds 1800
        讀取 reports、failure manifest、heartbeat、resume state，產生 Batch_Recovery_Plan.json / .md。

相容性：

- 不覆蓋 Stage-01~09 行為。
- heartbeat 預設關閉，避免改變既有 Batch Report version。
- 不改動 Foundation / CLI / SDK / Runtime API / Web UI Frozen 層。
