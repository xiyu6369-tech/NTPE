NTPE 1.0 Beta — Stage-01 Production Runtime
===========================================

新增內容：
- core/production_runtime/
  - RuntimeHost
  - RuntimeScheduler
  - RuntimeSessionManager
  - RuntimeCheckpointStore
  - RuntimeRecoveryManager
  - RuntimeMetrics
  - RuntimeTelemetry
  - Production Runtime Manifest
- tests/beta_stage_01/launcher_production_runtime_test.py

設計原則：
- Foundation v1.0 Frozen 後的上層產品化 Runtime。
- 不修改 Foundation Contract。
- 不覆蓋既有 Runtime / Knowledge / Intelligence 模組。
- 以增量方式新增 Production Runtime Host。

測試：
cd /d D:\Python\NTPE
python tests\beta_stage_01\launcher_production_runtime_test.py

Commit 建議：
feat(beta-stage-01): add production runtime host
