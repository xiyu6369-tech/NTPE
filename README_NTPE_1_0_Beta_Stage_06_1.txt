NTPE 1.0 Beta - Stage-06.1 Translation Command
================================================

新增 CLI translate 指令，支援 TXT 檔與資料夾批次翻譯入口。

套用方式：
1. 將本 ZIP 解壓到 D:\Python\NTPE
2. 執行測試：
   python tests\beta_stage_06_1\launcher_cli_translation_command_test.py

新增/修改：
- cli/main.py
- cli/parser.py
- cli/commands/*
- tests/beta_stage_06_1/launcher_cli_translation_command_test.py

命令範例：
- python -m cli translate input.txt --output output
- python -m cli translate input_folder --output output --resume
- python -m cli translate input_folder --provider nvidia --quality high
- python -m cli translate input_folder --dry-run --json

Commit 建議：
feat(beta-stage-06.1): add cli translation command
