NTPE Character Memory Engine v1.0

用途：
合併 Document Analyzer 產生的各卷角色候選資料，建立整套作品共用角色記憶庫。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

使用：
cd /d D:\Python\NTPE
python launcher_memory.py

輸入：
D:\Python\NTPE\analysis\*_character_memory_auto.json

手動鎖名表：
D:\Python\NTPE\character_override.json

輸出：
D:\Python\NTPE\memory\character_memory.json
D:\Python\NTPE\memory\character_memory_only.json
D:\Python\NTPE\memory\character_memory_report.txt
D:\Python\NTPE\memory\character_memory.csv

說明：
- character_memory.json：含 summary + characters，給系統使用
- character_memory_only.json：只有 characters，給翻譯器直接載入
- character_memory_report.txt：人工檢查用
- character_memory.csv：Excel 檢查用

如果要新增固定譯名，請修改 character_override.json。
