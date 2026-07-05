NTPE v0.9.1.1 Transactional Recovery Patch

用途：
修正 v0.9.1 failed_chunks 必須等整輪跑完才會寫入的問題。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

覆蓋檔案：
launcher_pipeline_recovery.py
engine\pipeline\recovery_pipeline.py

執行：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_pipeline_recovery.py

v0.9.1.1 修正：
- 每次 attempt 失敗立即寫入：
  failed_chunks\<file_stem>\chunk000004_attempt1.json

- chunk 最終失敗立即寫入：
  failed_chunks\<file_stem>\chunk000004.json

- 每個 chunk 狀態立即寫入：
  sessions\chunk_state\<file_stem>\chunk000004.json

- 中途 Ctrl+C / 關機 / Timeout 不會遺失已知失敗紀錄。

給 v0.9.2 Adaptive Recovery：
之後 Recovery 可以直接掃描：
failed_chunks\<file_stem>\chunk000004.json

注意：
已完成 translated chunk 仍會自動跳過。
