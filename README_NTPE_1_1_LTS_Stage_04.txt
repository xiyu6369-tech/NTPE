NTPE 1.1 LTS Stage-04: Translation QA / Korean Residue Check
==============================================================

新增正式 TXT 翻譯入口的 QA 保護層，用於降低以下問題：

- 韓文殘留
- 空譯文或過短譯文
- 重複行輸出

基本用法：

python ntpe_translate_txt.py input\小說.txt output --max-retries 5 --retry-base-seconds 10

QA 參數：

--no-qa
    關閉 QA 檢查。

--qa-fail-policy retry|fail|warn
    retry：QA 失敗時依 max-retries 重新翻譯。
    fail：QA 失敗時停止該 chunk 並寫入 resume state。
    warn：QA 失敗仍保存輸出，但 manifest 會保留 QA 警告。

--min-length-ratio 0.25
    譯文/原文最小字元比例。

--max-korean-chars 3
    允許殘留的韓文字元上限。

--max-repeated-lines 2
    同一非短行允許重複的上限。

本 Stage 採用增量更新，不覆蓋已凍結功能。
