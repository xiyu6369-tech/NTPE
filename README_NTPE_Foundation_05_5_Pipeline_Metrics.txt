NTPE Foundation-05.5 Pipeline Metrics
=====================================

增量更新內容：

1. 新增 core/pipeline/metrics.py
   - PipelineMetricRecord
   - PipelineMetricsSnapshot
   - PipelineMetricsCollector
   - collect_lifecycle_metrics
   - merge_metrics_snapshots
   - export_metrics_manifest
   - validate_metrics_snapshot

2. 新增 adapters/pipeline_metrics_adapter.py
   - build_pipeline_metrics_adapter
   - adapter_collect_lifecycle_metrics
   - adapter_export_metrics_manifest
   - adapter_validate_metrics_snapshot

3. 新增 tests/launcher_pipeline_metrics_test.py

設計原則：
- 不覆蓋 Foundation-05.4 lifecycle manager
- 不修改既有 registry/resolver/scheduler contract
- metrics 以讀取 lifecycle state/result 為主，不反向改寫 runtime state
- 保持 legacy metric input 相容：str、dict、PipelineMetricRecord

測試：
python tests\launcher_pipeline_metrics_test.py
