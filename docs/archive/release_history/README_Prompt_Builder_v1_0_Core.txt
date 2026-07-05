NTPE Prompt Builder v1.0 Core

用途：
根據 Project Profile、Character Database、Glossary、Knowledge Base 與 Chunk，自動產生 Prompt Package。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

測試：
cd /d D:\Python\NTPE
python launcher_prompt_builder.py

輸出：
D:\Python\NTPE\prompt_packages\prompt_package_sample.json

執行前需先存在：
profiles\passion_profile.json
memory\character_database.json
memory\character_match_dictionary.json
memory\glossary.json
memory\knowledge_base.json
