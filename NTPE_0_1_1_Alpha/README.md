# NTPE 0.1.1 Alpha

Novel Translator Professional Edition Foundation.

## 本版內容

- `launcher.py`：啟動入口
- `config/config_manager.py`：設定檔管理
- `core/logger.py`：Console + file logger
- `core/scheduler.py`：RPM Scheduler
- `core/exceptions.py`：統一例外類別

## 安裝與測試

請將本專案內容放在：

```text
D:\Python\NTPE\
```

執行：

```bat
cd /d D:\Python\NTPE
pip install -r requirements.txt
python launcher.py
```

成功會看到：

```text
NTPE 0.1.1 Alpha - Infrastructure OK
```
