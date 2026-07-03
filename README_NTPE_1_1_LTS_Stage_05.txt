NTPE 1.1 LTS Stage-05：Output Formatter / Taiwan Traditional Chinese Normalization

本階段以增量方式強化正式 TXT 小說翻譯入口，不破壞 NTPE 1.0 Stable 與 LTS Stage-01/02/03/04 相容性。

新增能力：
- Provider 輸出前綴清理，例如「以下是翻譯：」「譯文：」。
- 常見 ASCII 標點轉中文標點。
- 簡體常見字詞轉台灣繁體中文。
- 翻譯 chunk 與最終整合輸出皆套用 formatter。
- manifest 記錄 formatter 設定。

新增參數：
python ntpe_translate_txt.py input\小說.txt output --no-output-formatter --no-taiwan-normalization

建議正式翻譯時維持預設啟用 formatter。
