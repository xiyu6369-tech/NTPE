NTPE 1.0 Beta — Stage-08.5 Event Bus
====================================

Status: PASS
Foundation v1.0: Frozen compatible
Development mode: Incremental update

新增內容：
- integration/event_bus.py
- integration/event_dispatcher.py
- integration/event_subscriber.py
- integration/event_publisher.py
- integration/event_registry.py
- integration/event_context.py
- integration/event_models.py
- integration/event_filters.py
- tests/beta_stage_08_5/launcher_event_bus_test.py

功能：
- Central Event Bus
- Publish / Subscribe
- Event Routing
- Event Filtering
- Event Priority
- Sync / Async Event Dispatch
- Runtime / SDK / CLI / Plugin / Extension Event Integration

測試指令：
python tests\beta_stage_08_5\launcher_event_bus_test.py
python tests\beta_stage_08_4\launcher_extension_framework_test.py
python tests\beta_stage_08_3\launcher_plugin_integration_test.py
python tests\beta_stage_08_2\launcher_sdk_cli_bridge_test.py
python tests\beta_stage_08_1\launcher_runtime_integration_test.py
python tests\beta_stage_08_0\launcher_integration_core_test.py
python tests\beta_stage_07_8\launcher_sdk_packaging_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py
