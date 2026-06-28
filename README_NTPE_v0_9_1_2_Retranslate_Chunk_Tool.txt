NTPE v0.9.1.2 Retranslate Chunk Tool

用途：
修復「已成功但翻譯品質不合格」的指定 chunk。

適合情況：
- 譯文變成摘要
- 門鈴誤翻成電話鈴
- 大量漏翻
- 人名規則不夠穩
- 某個 chunk 需要單獨重翻

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
launcher_retranslate_chunk.py
engine\pipeline\retranslate_chunk.py

使用：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key

重翻 passion1 chunk 1：
python launcher_retranslate_chunk.py passion1_normalized.txt 1

輸出：
會覆蓋：
translated\passion1_normalized_chunk_000001_zh.txt

舊檔會備份為：
translated\passion1_normalized_chunk_000001_zh.bak.txt

注意：
建議不要和正在執行的 pipeline 同時處理同一個 chunk。
如果 pipeline 正在跑後面 chunk，可以等它停止或跑完後再重翻 chunk 1。
