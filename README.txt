NTPE Document Normalizer v1.0

用途：
整理 TXT 文件，特別適合韓文小說原文或翻譯後文本在進入 NTPE 翻譯流程前先清理。

安裝：
1. 解壓縮到：
   D:\Python\NTPE\

2. 在 CMD 執行：
   cd /d D:\Python\NTPE
   pip install -r requirements.txt

使用：
1. 把要整理的 TXT 放進：
   D:\Python\NTPE\input

2. 執行：
   python launcher.py

3. 整理後檔案會出現在：
   D:\Python\NTPE\output

資料夾說明：
input   ：放原始 TXT
output  ：輸出整理後 TXT
backup  ：自動備份原始 TXT
logs    ：執行紀錄

v1.0 功能：
- 自動偵測 utf-8 / cp949 / euc-kr / big5 / gb18030
- 移除 BOM、NUL、奇怪控制字元
- 簡體轉台灣繁體
- 標點統一為中文標點
- 引號統一為「」
- 多餘空白與過多空行清理
- 原始檔自動備份
