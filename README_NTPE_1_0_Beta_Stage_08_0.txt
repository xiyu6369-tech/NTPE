NTPE 1.0 Beta — Stage-08.0 Integration Core
============================================

Status: PASS
Foundation v1.0: Frozen compatible
CLI Freeze: Compatible
SDK Stage-07: Compatible

新增內容：
- integration/manifest.py
- integration/contracts.py
- integration/registry.py
- integration/context.py
- integration/core.py
- tests/beta_stage_08_0/launcher_integration_core_test.py

目標：
建立 Stage-08 Integration & Extension 的核心整合層，讓 Runtime、CLI、SDK、Plugin 可以透過穩定 registry/context/result contract 串接。

測試：
python tests\beta_stage_08_0\launcher_integration_core_test.py
python tests\beta_stage_07_8\launcher_sdk_packaging_test.py
python tests\beta_stage_07_7\launcher_sdk_plugin_api_test.py
python tests\beta_stage_07_6\launcher_sdk_configuration_api_test.py
python tests\beta_stage_07_5\launcher_sdk_error_handling_api_test.py
python tests\beta_stage_07_4\launcher_sdk_streaming_api_test.py
python tests\beta_stage_07_3\launcher_sdk_batch_api_test.py
python tests\beta_stage_07_2\launcher_sdk_translation_api_test.py
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_07_0\launcher_sdk_core_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py
