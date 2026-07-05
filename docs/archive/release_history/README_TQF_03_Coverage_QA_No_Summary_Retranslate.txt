NTPE TQF-03 Coverage QA + No-Summary Retranslate

用途：
解決模型摘要化與段落壓縮問題，例如 source 43 段被翻成 4 段。

新增檔案：
core\quality\coverage_analyzer.py
core\quality\coverage_checker.py
rules\coverage_rules.json
launcher_coverage_test.py

覆蓋檔案：
core\quality\__init__.py
engine\pipeline\retranslate_chunk.py

測試：
cd /d D:\Python\NTPE

先看目前 coverage：
python launcher_coverage_test.py

重翻 chunk 1：
python launcher_retranslate_chunk.py passion1_normalized.txt 1

再看 coverage：
python launcher_coverage_test.py

再跑總分：
python launcher_quality_benchmark.py

TQF-03 目標：
- translation_paragraphs 明顯增加
- coverage 分數提高
- overall_score 提高
- source 43 段不再被壓成 4 段
