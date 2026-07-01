# NTPE Foundation-04.5 Pipeline Execution Trace

## 目的

Foundation-04.5 新增 Pipeline Execution Trace，用於記錄 Production Pipeline、Adapter System、Plugin System、Context/Prompt/Narrative/Quality Pipeline 的執行事件。

本階段為增量更新，不取代 Foundation-04.4 Pipeline State Contract。

## 新增檔案

```text
core/pipeline_execution_trace.py
core/pipeline_execution_trace_adapter.py
tests/launcher_pipeline_execution_trace_test.py
docs/foundation_04_5_pipeline_execution_trace.md
```

## Trace Contract 標準欄位

```python
{
    "trace_version": "04.5",
    "trace_id": "ntpe-trace-...",
    "events": [],
    "summary": {
        "event_count": 0,
        "stage_event_count": 0,
        "plugin_event_count": 0,
        "adapter_event_count": 0,
        "error_event_count": 0,
        "warning_event_count": 0,
    },
    "runtime": {
        "created_at": None,
        "updated_at": None,
        "completed_at": None,
    },
}
```

## Event Contract 標準欄位

```python
{
    "index": 1,
    "type": "stage | plugin | adapter | payload | quality | narrative | prompt | context | error | warning | trace",
    "status": "created | started | running | completed | failed | skipped | attached | applied | validated | warning",
    "name": "context",
    "message": "",
    "time": "UTC ISO timestamp",
    "metadata": {},
}
```

## 向下相容

支援舊欄位自動轉換：

```text
id -> trace_id
trace -> events
event_type -> type
event -> status
stage/plugin/adapter -> name
```

未知欄位會保留，不會刪除。

## 測試方式

```bat
cd /d D:\Python\NTPE
python tests\launcher_pipeline_execution_trace_test.py
```

預期輸出最後為：

```text
PASS
```
