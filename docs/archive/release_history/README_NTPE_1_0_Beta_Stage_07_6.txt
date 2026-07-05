NTPE 1.0 Beta — Stage-07.6 SDK Configuration API
=================================================

Status: PASS
Compatibility: Additive update. Foundation v1.0 and CLI Stage-06.9 remain frozen-compatible.

新增內容：
- sdk/config.py
- sdk/config_builder.py
- sdk/config_loader.py
- sdk/config_validator.py
- sdk/config_models.py
- tests/beta_stage_07_6/launcher_sdk_configuration_api_test.py

主要能力：
- SDKConfig 統一設定物件
- SDKConfigBuilder fluent builder
- Provider / Runtime / Translation / Batch / Streaming configuration
- JSON serialization / deserialization
- SDKConfigValidator validation result
- Runtime payload export
- Secret masking by default

測試指令：
python tests\beta_stage_07_6\launcher_sdk_configuration_api_test.py
python tests\beta_stage_07_5\launcher_sdk_error_handling_api_test.py
python tests\beta_stage_07_4\launcher_sdk_streaming_api_test.py
python tests\beta_stage_07_3\launcher_sdk_batch_api_test.py
python tests\beta_stage_07_2\launcher_sdk_translation_api_test.py
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_07_0\launcher_sdk_core_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py

Commit 建議：
git add sdk tests\beta_stage_07_6 README_NTPE_1_0_Beta_Stage_07_6.txt
git commit -m "Stage-07.6 SDK Configuration API"
git push origin main
git tag beta-stage-07.6-sdk-configuration-api
git push origin beta-stage-07.6-sdk-configuration-api
