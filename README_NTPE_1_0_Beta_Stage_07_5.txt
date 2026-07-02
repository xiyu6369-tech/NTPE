NTPE 1.0 Beta — Stage-07.5 SDK Error Handling API
==================================================

Status: PASS
Compatibility: Additive, backward compatible

Scope
-----
Stage-07.5 adds a stable SDK error handling layer without changing the frozen
Foundation v1.0 contracts or Stage-06 CLI behavior.

Added files
-----------
sdk/error_codes.py
sdk/error_models.py
sdk/error_response.py
sdk/errors.py
tests/beta_stage_07_5/launcher_sdk_error_handling_api_test.py
README_NTPE_1_0_Beta_Stage_07_5.txt

Updated files
-------------
sdk/__init__.py
sdk/exceptions.py

Validation
----------
python tests\beta_stage_07_5\launcher_sdk_error_handling_api_test.py
python tests\beta_stage_07_4\launcher_sdk_streaming_api_test.py
python tests\beta_stage_07_3\launcher_sdk_batch_api_test.py
python tests\beta_stage_07_2\launcher_sdk_translation_api_test.py
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_07_0\launcher_sdk_core_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py

Expected result
---------------
Stage-07.5 SDK Error Handling API  PASS
Stage-07.4 SDK Streaming API       PASS
Stage-07.3 SDK Batch API           PASS
Stage-07.2 SDK Translation API     PASS
Stage-07.1 SDK Session API         PASS
Stage-07.0 SDK Core                PASS
Stage-06.9 CLI Freeze              PASS
Foundation Freeze                  PASS
