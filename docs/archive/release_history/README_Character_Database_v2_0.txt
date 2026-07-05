NTPE Character Database v2.0

使用：
cd /d D:\Python\NTPE
python launcher_character_db.py

輸出：
memory\character_database.json
memory\character_match_dictionary.json
memory\character_database_report.txt
memory\character_database_index.csv

核心規則：
- 全名翻全名
- 名字翻名字
- 姓氏翻姓氏
- 韓文三字姓名不拆
- 英文姓名使用 regex safe pattern
