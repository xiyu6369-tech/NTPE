NTPE Prompt Package Spec v1.0

用途：
定義 Prompt Builder、Translation Engine、QA Engine、Context Manager 之間共用的資料格式。

這不是翻譯器本體，而是 AI Layer 的共同介面。

放置位置：
解壓縮後，把內容放進：
D:\Python\NTPE\

新增檔案：
schemas\prompt_package_schema_v1.json
examples\prompt_package_example_v1.json
core\prompt_package_validator.py
README_Prompt_Package_Spec_v1_0.txt

驗證範例：
cd /d D:\Python\NTPE
python core\prompt_package_validator.py examples\prompt_package_example_v1.json

通過時會顯示：
PASS: valid NTPE Prompt Package
