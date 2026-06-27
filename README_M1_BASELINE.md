# NTPE M1 Baseline Combination

來源：NTPE(2).zip 的完整核心模組。

本包用途：建立 M1 Baseline 候選，不新增功能。

## 包含

- core/translator.py
- core/prompt_engine.py
- core/rules.py
- core/chunker.py
- core/formatter.py
- core/validator.py
- core/glossary.py
- core/encoding.py
- engine/nvidia.py
- config/default_config.json
- config/models.json
- config/paths.json
- rules/*.json
- data/glossary.txt

## 小修

- 移除 core/rules.py 內「三天三夜 -> 三天」的語意替換。
  原因：這類內容若是 AI 新增，應由 validator 擋下重翻，不應自動改成另一個看似合理的句子。

## 注意

- 本包不包含 config/config.json，避免覆蓋你的 NVIDIA API Key。
- 測試前請刪除 output/測試_zh.txt 與 cache/progress.json。
