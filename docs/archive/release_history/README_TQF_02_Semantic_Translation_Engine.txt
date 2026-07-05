NTPE TQF-02 Semantic Translation Engine

用途：
把高風險韓文語義點鎖進 Prompt Package，降低誤譯、摘要化與幻覺。

新增檔案：
core\quality\semantic_engine.py
core\quality\__init__.py
rules\semantic_translation_rules.json
launcher_semantic_test.py

覆蓋檔案：
core\prompt_builder\prompt_builder.py
core\prompt_builder\prompt_renderer.py
core\prompt_builder\package_builder.py

測試：
cd /d D:\Python\NTPE
python launcher_semantic_test.py

成功應看到：
semantic_matches: 5+
초인종 -> 門鈴
두어 술 떴 -> 才吃了幾口早餐
군화 -> 軍靴
연립주택 -> 老舊連棟住宅
역병신 -> 像把瘟神迎進門
PASS

接著重翻 chunk 1：
python launcher_retranslate_chunk.py passion1_normalized.txt 1

再跑品質分數：
python launcher_quality_benchmark.py
