NTPE TQF-03.2 Best Effort Save + UltraSplit

覆蓋：
engine\pipeline\retranslate_chunk.py
rules\coverage_rules.json

使用：
cd /d D:\Python\NTPE
python launcher_retranslate_chunk.py passion1_normalized.txt 1
python launcher_coverage_test.py
python launcher_quality_benchmark.py

重點：
- 標題鎖定為《PASSION》第一卷
- 分段更小，降低摘要化
- 若 coverage 未達嚴格門檻，保存最佳版本，不再卡死
- 可能回傳 best_effort，代表有輸出但後續仍需 TQF-04/05 改善
