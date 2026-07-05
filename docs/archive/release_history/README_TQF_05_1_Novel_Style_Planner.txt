NTPE TQF-05.1 Novel Style Planner

用途：
在翻譯前建立出版級小說翻譯策略，降低摘要化、機翻腔與畫面流失。

新增檔案：
core\quality\novel_style_planner.py
rules\novel_style_rules.json
launcher_style_planner_test.py

覆蓋檔案：
core\quality\__init__.py
core\prompt_builder\prompt_builder.py
core\prompt_builder\prompt_renderer.py
core\prompt_builder\package_builder.py

測試：
cd /d D:\Python\NTPE
python launcher_style_planner_test.py

成功後可重翻 chunk 1：
python launcher_retranslate_chunk.py passion1_normalized.txt 1
python launcher_semantic_repair.py
python launcher_quality_benchmark.py

目標：
- 讓 Prompt Package 帶入 novel_style_plan
- 翻譯前提示模型保留動作、心理、比喻、氛圍與出版級語感
