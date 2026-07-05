NTPE Knowledge Base Builder v1.0

用途：
整合 Character Memory 與 Glossary，建立翻譯器與 QA 引擎可共用的知識庫。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

使用：
cd /d D:\Python\NTPE
python launcher_kb.py

輸入：
D:\Python\NTPE\memory\character_memory.json
D:\Python\NTPE\memory\glossary.json

輸出：
D:\Python\NTPE\memory\knowledge_base.json
D:\Python\NTPE\memory\knowledge_base_only.json
D:\Python\NTPE\memory\knowledge_base_report.txt
D:\Python\NTPE\memory\knowledge_base_index.csv

說明：
- knowledge_base.json：完整知識庫，含 summary
- knowledge_base_only.json：精簡版，給翻譯器直接載入
- knowledge_base_report.txt：人工檢查用
- knowledge_base_index.csv：Excel 檢查用

主要內容：
- characters：角色記憶庫
- glossary：術語庫
- aliases：別名索引
- locked_index：已鎖定譯名索引
- prompt_dictionary：給翻譯 Prompt 使用的固定譯名表
