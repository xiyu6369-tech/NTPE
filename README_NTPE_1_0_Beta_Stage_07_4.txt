NTPE 1.0 Beta — Stage-07.4 SDK Streaming API
=============================================

Status: PASS
Compatibility: Foundation v1.0 Frozen / Stage-06.9 CLI Freeze / Stage-07.0-07.3 SDK compatible

新增內容：
- sdk/stream.py
- sdk/stream_event.py
- sdk/stream_models.py
- sdk/stream_response.py
- sdk/stream_session.py
- tests/beta_stage_07_4/launcher_sdk_streaming_api_test.py

主要能力：
- SDK Streaming Translation
- Token / Segment / Progress Event
- Event Callback
- Async Stream Collection
- Stream File Translation
- Error Event Handling
- Runtime Bridge / Translation API Reuse

回歸測試：
python tests\beta_stage_07_4\launcher_sdk_streaming_api_test.py
python tests\beta_stage_07_3\launcher_sdk_batch_api_test.py
python tests\beta_stage_07_2\launcher_sdk_translation_api_test.py
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_07_0\launcher_sdk_core_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py
