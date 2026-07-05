NTPE v0.9.1 Production Recovery

用途：
修復 v0.9.0 Production Pipeline 遇到 NVIDIA API Timeout 時會中止全流程的問題。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_pipeline_recovery.py
engine\pipeline\recovery_pipeline.py

執行：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_pipeline_recovery.py

v0.9.1 功能：
- Timeout / API 失敗自動重試
- 單一 chunk 失敗不終止全流程
- 已存在 translated chunk 自動跳過
- 重跑時避免重翻已完成 chunk
- 失敗 chunk 記錄到 failed_chunks\
- 終端機即時顯示進度
- 保留 Session JSON

輸出：
translated\
translation_cache\
prompt_packages\
sessions\
failed_chunks\
final_output\
logs\recovery_pipeline.log

注意：
這不是完整 Resume Engine，但已可避免從頭重翻成功 chunk。
v0.9.2 會再加入正式 QA Retry 與更完整的 Session Resume。
