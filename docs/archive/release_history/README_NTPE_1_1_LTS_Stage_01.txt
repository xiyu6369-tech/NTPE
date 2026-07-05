NTPE 1.1 LTS Stage-01 — 正式小說 TXT 翻譯入口
================================================

新增入口：
  python ntpe_translate_txt.py input\novel.txt output

功能：
- 讀取 TXT 小說檔案。
- 自動偵測常見編碼：UTF-8 / CP949 / EUC-KR / Big5。
- 自動分塊。
- 產生 NTPE Prompt Package。
- 呼叫既有 TranslationEngine，不破壞 NTPE 1.0 Stable。
- 支援 chunk resume。
- 輸出完整繁中譯文與 manifest。

測試模式：
  python ntpe_translate_txt.py input\novel.txt output --dry-run

正式翻譯前請先設定：
  set NVIDIA_API_KEY=你的真正NVIDIA_API_KEY
