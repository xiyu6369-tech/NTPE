NTPE TQF-03.1 Title Lock + Coverage Strict Patch

用途：
修正 TQF-03 後仍出現：
- 패션 1 被翻成「時尚 1」
- length_ratio 0.64 仍被判定通過

新增/覆蓋檔案：
rules\coverage_rules.json
engine\pipeline\retranslate_chunk.py

測試：
cd /d D:\Python\NTPE
python launcher_retranslate_chunk.py passion1_normalized.txt 1
python launcher_coverage_test.py
python launcher_quality_benchmark.py

預期改善：
- 譯文開頭應為：《PASSION》第一卷
- 不應再出現「時尚 1」
- coverage ratio 低於 0.70 時會重試，不再直接通過
