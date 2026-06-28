NTPE Pipeline Engine v1.0 Core

用途：
建立 NTPE 的流程控制中心，負責串接 Project Profile、Prompt Builder、Translation Engine 與 Session。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_pipeline.py
engine\pipeline\*.py

執行前準備：
1. 確認 Prompt Builder 已可正常執行：
   python launcher_prompt_builder.py

2. 確認 Translation Engine 已可正常執行：
   set NVIDIA_API_KEY=你的Key
   python launcher_translate.py

3. 執行 Pipeline Demo：
   python launcher_pipeline.py

輸出：
sessions\SESSION_*.json
logs\pipeline.log
prompt_packages\SESSION_*_chunk_000001.json
translated\*_zh.txt
translation_cache\*_result.json

v1.0 Core 功能：
- Project Manager
- Pipeline Session
- Stage Result
- Event Logger
- Demo Chunk
- Prompt Builder Stage
- Translation Engine Stage

注意：
這版先驗證 Pipeline 骨架，不直接批次翻整本。
下一版才加入：
- 掃描 normalized files
- 自動切 chunk
- resume
- merge
- QA retry
