NTPE 1.1 LTS Stage-02 Resume / Retry 強化
=========================================

新增能力：
1. TXT 小說翻譯支援 chunk-level resume state。
2. 已完成 chunk 會依 source_hash 與輸出檔檢查自動跳過。
3. NVIDIA 503 / 429 / ResourceExhausted / timeout 類錯誤會自動 retry。
4. 支援可調整 retry 參數。

基本用法：
python ntpe_translate_txt.py input\小說.txt output

可選參數：
python ntpe_translate_txt.py input\小說.txt output --max-retries 5 --retry-base-seconds 10

測試模式：
python ntpe_translate_txt.py input\小說.txt output --dry-run

Resume state 位置：
output\小說_resume_state.json

相容性：
本 Stage 僅增量強化 LTS TXT 翻譯入口，不覆蓋 NTPE 1.0 Stable Frozen 層。
