NTPE v0.9.0 Production Pipeline

用途：
把目前已完成的 Prompt Builder 與 Translation Engine 串成可處理 normalized TXT 的生產流程。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_pipeline_production.py
engine\pipeline\production_pipeline.py
engine\pipeline\chunk_engine.py
engine\pipeline\merger.py

執行前準備：
1. 確認 output\ 裡有 *_normalized.txt
2. 確認 Character Database / Knowledge Base 已建立
3. 確認 Project Profile 已建立
4. 設定 NVIDIA API Key

CMD：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_pipeline_production.py

輸出：
prompt_packages\
translated\
translation_cache\
sessions\
logs\production_pipeline.log
final_output\*_zh.txt

v0.9.0 功能：
- 掃描 output\*_normalized.txt
- 段落式切 chunk
- 逐 chunk 建 Prompt Package
- 逐 chunk 呼叫 Translation Engine
- 保存 Session
- 合併每本 final output

尚未包含：
- 完整 Resume
- QA Retry
- GUI
- OpenCC 後處理
- 失敗 chunk 自動分裂重試

建議：
先用小 TXT 測試，不要直接跑六本全量。
確認流程正常後，再逐步放大。
