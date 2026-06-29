NTPE v1.0.1 Pipeline Safety Patch

修正：
- 即時寫入 reports\pipeline_v1_live_report.json
- quality < 95 改標 needs_review，不再當作正式 done
- 低分 chunk 寫入 reports\quality_failed_chunks.json
- 缺少 normalized file 不再讓整個 pipeline 崩潰
- Ctrl+C 中斷時保留 live report

覆蓋：
launcher_pipeline_v1.py
engine\pipeline\pipeline_v1.py

使用：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_pipeline_v1.py

注意：
已存在 translated chunk 仍會 SKIP。
要重跑低品質 chunk，需先移走對應 translated chunk。
