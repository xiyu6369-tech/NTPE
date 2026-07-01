# NTPE Foundation-04.4 Pipeline State Contract

## 目的

Foundation-04.4 新增穩定的 Pipeline State Contract，用於統一 Production Pipeline、Adapter System、Plugin System 在執行期間共享的狀態格式。

本階段為增量更新，不取代 Foundation-04.3 Context Contract。

## 新增檔案

```text
core/pipeline_state_contract.py
core/pipeline_state_adapter.py
tests/launcher_pipeline_state_contract_test.py
docs/foundation_04_4_pipeline_state_contract.md
```

## State Contract 標準欄位

```python
{
    "state_version": "04.4",
    "status": "initialized | running | completed | failed | skipped | paused",
    "current_stage": None,
    "completed_stages": [],
    "failed_stages": [],
    "adapter_trace": [],
    "plugin_trace": [],
    "errors": [],
    "warnings": [],
    "counters": {},
    "runtime": {},
    "payload": {},
}
```

## 向下相容

支援舊欄位自動轉換：

```text
stage -> current_stage
done_stages -> completed_stages
failures -> errors
```

未知欄位會保留，不會刪除。

## 測試方式

```bat
cd /d D:\Python\NTPE
python tests\launcher_pipeline_state_contract_test.py
```

預期輸出最後為：

```text
PASS
```
