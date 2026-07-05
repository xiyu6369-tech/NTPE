NTPE 1.0 Beta — Stage-10.2 Service Discovery
============================================

新增內容
--------
- platform_services/service_discovery.py
- tests/beta_stage_10_2/launcher_service_discovery_test.py

功能
----
- 新增 PlatformServiceDiscovery。
- 支援依 service name、status、tag、dependency、metadata 查找平台服務。
- 新增 ServiceDiscoveryQuery 與 ServiceDiscoveryResult。
- 保持對 PlatformServiceRegistry 的唯讀查詢，不修改既有 frozen API。

相容性
------
Foundation v1.0: Frozen / compatible
CLI: Frozen / compatible
SDK: Complete / compatible
Integration: Frozen / compatible
Workflow: Frozen / compatible

測試
----
python tests/beta_stage_10_2/launcher_service_discovery_test.py
python tests/beta_stage_10_1/launcher_platform_config_test.py
python tests/beta_stage_10_0/launcher_platform_services_test.py
python tests/beta_stage_09_8/launcher_workflow_freeze_test.py
