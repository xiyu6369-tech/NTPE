NTPE v1.1 / TQF-06.1 Novel Prompt Engine

用途：
把 Prompt Builder 升級成出版級韓文小說翻譯 Prompt Framework。

新增：
core\quality\novel_prompt_engine.py
rules\novel_prompt_engine_rules.json
launcher_novel_prompt_test.py

覆蓋：
core\quality\__init__.py
core\prompt_builder\prompt_builder.py
core\prompt_builder\prompt_renderer.py
core\prompt_builder\package_builder.py

測試：
cd /d D:\Python\NTPE
python launcher_novel_prompt_test.py

成功後，可重跑單一 chunk：
python launcher_retranslate_chunk.py passion1_normalized.txt 1
python launcher_semantic_repair.py
python launcher_quality_benchmark.py

注意：
這版先升級 Prompt 結構，不修改 Pipeline。
