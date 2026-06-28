NTPE v0.9.2 Adaptive Chunk Recovery

用途：
針對 v0.9.1 失敗的 chunk，自動切成較小 subchunks 重試，成功後合併回原 chunk 輸出檔。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_adaptive_recovery.py
engine\pipeline\adaptive_recovery.py

執行前：
請先跑過 v0.9.1，並確認 failed_chunks\ 有 *_failed_chunks.json。

執行：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_adaptive_recovery.py

功能：
- 讀取失敗 chunk
- 自動分割成 1400 字左右 subchunks
- 逐段重翻
- 成功後合併回原 chunk output
- 已完成 chunk 自動跳過

注意：
這版只處理 failed chunks，不重新跑整本。
