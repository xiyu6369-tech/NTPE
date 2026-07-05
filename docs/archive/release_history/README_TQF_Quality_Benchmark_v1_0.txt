NTPE TQF Quality Benchmark v1.0

用途：
建立翻譯品質的可量化基準，先評估 Prompt Package + 譯文，不改動既有 Pipeline。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_quality_benchmark.py
core\quality\__init__.py
core\quality\quality_benchmark.py
rules\semantic_quality_rules.json
quality_reports\

預設測試：
cd /d D:\Python\NTPE
python launcher_quality_benchmark.py

預設會檢查：
prompt_packages\passion1_normalized_chunk_000001.json
translated\passion1_normalized_chunk_000001_zh.txt

也可以指定檔案：
python launcher_quality_benchmark.py prompt_packages\xxx.json translated\xxx.txt

輸出：
quality_reports\quality_benchmark_*.json
quality_reports\quality_benchmark_*.txt

目前會評估：
- Structure：標題是否被當成正文，例如 패션 1 → 時尚的...
- Semantic：초인종 → 門鈴、군화 → 軍靴等語義鎖
- Coverage：譯文是否過短、段落是否壓縮
- Hallucination：早餐/幾口飯是否被誤譯成喝酒
- Style：段落是否過長、節奏是否被壓扁

建議：
這一版先用來量化現有翻譯問題。
下一步 TQF-02 才把 Semantic Engine 接回 Prompt Builder / QA Retry。
