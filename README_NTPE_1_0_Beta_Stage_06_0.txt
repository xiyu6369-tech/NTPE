NTPE 1.0 Beta - Stage-06.0 CLI Core
====================================

新增 cli/ 核心命令框架，提供：

- python -m cli --help
- python -m cli version
- python -m cli doctor
- python -m cli doctor --json

本階段只建立 CLI Core，不直接接入翻譯命令；後續 Stage-06.1 開始接入 translate/resume 等產品命令。

Commit:
feat(beta-stage-06.0): add cli core
