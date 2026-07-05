NTPE v1.0 Production Pipeline

用途：
把 TQF-01～TQF-05 串成一鍵式生產流程。

新增檔案：
launcher_pipeline_v1.py
engine\pipeline\pipeline_v1.py

執行：
cd /d D:\Python\NTPE
set NVIDIA_API_KEY=你的Key
python launcher_pipeline_v1.py

流程：
1. 掃描 output\*_normalized.txt
2. 切 chunk
3. Prompt Builder
4. Translation Engine
5. Semantic QA
6. Semantic Repair
7. Coverage QA
8. Style Expansion
9. 再做 Semantic Repair
10. Chunk Merge
11. Pipeline Report

輸出：
translated\
final_output\
reports\pipeline_v1_report_*.json
sessions\pipeline_v1\
logs\pipeline_v1.log

注意：
- 已存在 translated chunk 會跳過。
- 品質修復只會對新翻譯 chunk 自動執行。
- 若要強制重新處理某個 chunk，請先移走該 translated chunk 檔。
