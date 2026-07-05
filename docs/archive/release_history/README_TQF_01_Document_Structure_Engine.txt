NTPE TQF-01 Document Structure Engine

用途：
解決「패션 1」被當成正文翻譯，甚至誤譯為「時尚的……」的問題。

放置位置：
解壓縮後，把內容複製到：
D:\Python\NTPE\

新增檔案：
core\quality\__init__.py
core\quality\structure_engine.py
rules\document_structure_rules.json
launcher_structure_test.py
README_TQF_01_Document_Structure_Engine.txt

覆蓋檔案：
core\prompt_builder\prompt_builder.py
core\prompt_builder\prompt_renderer.py
core\prompt_builder\package_builder.py

測試：
cd /d D:\Python\NTPE
python launcher_structure_test.py

成功應顯示：
has_title: True
source: 패션 1
target: 《PASSION》第一卷
PASS

功能：
- 偵測第一個非空白行是否為作品標題。
- 將 패션 1 固定識別為標題。
- 在 Prompt Package 的 source.document_structure 中保存結構資訊。
- 在 Prompt 中加入文件結構規則，要求標題獨立成行，不可併入正文。
- 鎖定 패션 在標題中譯為 PASSION，不可譯為「時尚」。
