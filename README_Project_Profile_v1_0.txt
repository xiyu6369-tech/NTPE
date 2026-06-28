NTPE Project Profile v1.0

用途：
建立 NTPE 專案級設定，供 Prompt Builder、Translation Engine、QA Engine 使用。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
profiles\passion_profile.json
schemas\project_profile_schema_v1.json
core\project_profile.py
launcher_profile.py
README_Project_Profile_v1_0.txt

測試：
cd /d D:\Python\NTPE
python launcher_profile.py

或：

python core\project_profile.py profiles\passion_profile.json

成功會顯示：
PASS: valid NTPE Project Profile
