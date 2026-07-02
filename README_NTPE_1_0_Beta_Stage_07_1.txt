NTPE 1.0 Beta — Stage-07.1 SDK Session API
===========================================

Status: PASS
Type: Additive SDK update
Compatibility:
- Foundation v1.0 Frozen: preserved
- Stage-06.9 CLI Freeze: preserved
- Stage-07.0 SDK Core: preserved

Added files:
- sdk/session.py
- sdk/exceptions.py
- tests/beta_stage_07_1/launcher_sdk_session_api_test.py

Updated files:
- sdk/__init__.py

New public SDK APIs:
- SDKSession
- SDKSessionStatus
- create_session()
- build_sdk_session_manifest()
- SDKError
- SDKSessionError

Validated capabilities:
- SDK Session Created
- SDK Runtime Started
- SDK Progress
- SDK Resume
- SDK Result
- SDK Callback
- Backward Compatible

Test commands:
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py

Commit suggestion:
git add sdk tests\beta_stage_07_1 README_NTPE_1_0_Beta_Stage_07_1.txt
git commit -m "Stage-07.1 SDK Session API"
git push origin main
git tag beta-stage-07.1-sdk-session-api
git push origin beta-stage-07.1-sdk-session-api
