NTPE Glossary Builder v1.0

用途：
合併 Document Analyzer 產生的各卷術語候選資料，建立整套作品共用術語庫。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

使用：
cd /d D:\Python\NTPE
python launcher_glossary.py

輸入：
D:\Python\NTPE\analysis\*_glossary_auto.json

手動術語表：
D:\Python\NTPE\glossary_override.json

輸出：
D:\Python\NTPE\memory\glossary.json
D:\Python\NTPE\memory\glossary_only.json
D:\Python\NTPE\memory\glossary_report.txt
D:\Python\NTPE\memory\glossary.csv

說明：
- glossary.json：含 summary + terms，給系統使用
- glossary_only.json：只有 terms，給翻譯器直接載入
- glossary_report.txt：人工檢查用
- glossary.csv：Excel 檢查用

分類：
- abbreviation：英文縮寫，例如 CIA / VIP
- code：英數混合代碼，例如 M4A1
- proper_english_term：英文專有詞
- english_term：一般英文詞
- unknown：其他

如果要新增固定術語，請修改 glossary_override.json。
