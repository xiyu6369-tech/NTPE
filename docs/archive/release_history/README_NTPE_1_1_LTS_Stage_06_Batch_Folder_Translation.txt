NTPE 1.1 LTS Stage-06：Batch Folder Translation
================================================

新增內容：
- ntpe_translate_batch.py
- lts/batch_translation_runtime.py
- tests/lts_stage_06/

啟動方式：
python ntpe_translate_batch.py input output

常用參數：
python ntpe_translate_batch.py input output --recursive
python ntpe_translate_batch.py input output --glossary glossary.txt --character-memory memory\character_memory_lts.json
python ntpe_translate_batch.py input output --max-retries 5 --retry-base-seconds 10
python ntpe_translate_batch.py input output --qa-fail-policy retry --max-korean-chars 3 --min-length-ratio 0.25

功能：
- 掃描整個 input 資料夾內的 .txt
- 支援自然排序
- 支援遞迴掃描
- 自動略過已存在且非空的 *_zh.txt
- 每個檔案沿用 Stage-01~05 的 TXT Runtime、Resume、Retry、Glossary、QA、Formatter
- 完成後產生 output/reports/Batch_Translation_Report.json
- 完成後產生 output/reports/Batch_Translation_Report.md

相容性：
- 不修改 Foundation v1.0 Frozen 層
- 不修改 CLI Frozen 層
- 不修改 SDK Frozen 層
- 不破壞既有 ntpe_translate_txt.py 入口
- 採用增量新增方式
