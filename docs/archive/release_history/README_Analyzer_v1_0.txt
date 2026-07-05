NTPE Document Analyzer v1.0

用途：
分析 Document Normalizer 輸出的 TXT，產生翻譯前置資料。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

安裝：
cd /d D:\Python\NTPE
pip install -r requirements.txt

使用：
1. 先執行 Normalizer：
   python launcher.py

2. 再執行 Analyzer：
   python launcher_analyzer.py

輸入位置：
D:\Python\NTPE\output

輸出位置：
D:\Python\NTPE\analysis

輸出檔案：
- *_analysis.json
- *_report.txt
- *_statistics.csv
- *_character_memory_auto.json
- *_glossary_auto.json

v1.0 分析項目：
- 基本字數、行數、段落數
- 韓文 / 中文 / 日文 / 英文比例
- 對話比例估算
- 章節偵測
- 疑似人物名偵測
- 英文術語偵測
- 重複段落 / 重複句子偵測
- 亂碼 / 損壞偵測
