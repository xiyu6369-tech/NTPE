NTPE TQF-04 Semantic QA + Auto Repair

用途：
針對已翻譯結果做語義檢查與保守自動修復，不重翻整段。

新增檔案：
core\quality\semantic_qa.py
core\quality\semantic_repair.py
rules\semantic_repair_rules.json
launcher_semantic_repair.py

覆蓋檔案：
core\quality\__init__.py

測試：
cd /d D:\Python\NTPE
python launcher_semantic_repair.py
python launcher_quality_benchmark.py

目前處理：
- 군화：避免弱化為鞋子
- 역병신：避免弱化為不舒服/不對勁
- 豆子從筷子掉落：避免誤成筷子掉落
- 英文雙引號：轉成中文引號「」

注意：
這是保守修復，不會大幅改寫整段。
