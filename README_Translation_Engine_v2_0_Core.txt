NTPE Translation Engine v2.0 Core

用途：
讀取 Prompt Package，呼叫 NVIDIA API，輸出譯文並保存翻譯快取。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_translate.py
core\translation_engine\*.py

執行前準備：
1. 需先產生 Prompt Package：
   python launcher_prompt_builder.py

2. 設定 NVIDIA API Key：
   Windows CMD：
   set NVIDIA_API_KEY=你的Key

   PowerShell：
   $env:NVIDIA_API_KEY="你的Key"

3. 執行：
   python launcher_translate.py

輸入：
prompt_packages\prompt_package_sample.json

輸出：
translated\*_zh.txt
translation_cache\*_result.json
logs\translation_engine_log.txt

v2.0 Core 功能：
- 讀取 Prompt Package
- 呼叫 NVIDIA Chat Completions API
- 支援 RPM 限速
- 保存譯文
- 保存翻譯快取
- 輕量 QA 檢查：韓文殘留、長度偏短、鎖定譯名缺失

注意：
正式 QA Engine 之後會獨立開發，本版只提供基礎檢查。
