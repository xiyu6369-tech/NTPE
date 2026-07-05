NTPE 1.0 Beta — Stage-07.3 SDK Batch API
=========================================

Status: PASS
Compatibility: Additive update; Foundation v1.0 Frozen and Stage-06.9 CLI Freeze remain compatible.

新增內容
--------
- sdk/batch.py
- sdk/batch_models.py
- sdk/batch_request.py
- sdk/batch_response.py
- tests/beta_stage_07_3/launcher_sdk_batch_api_test.py

主要能力
--------
- SDK 多文字批次翻譯
- SDK 多檔案批次翻譯
- BatchRequest / BatchResponse
- BatchItem / BatchOptions / BatchProgress / BatchResult
- 批次進度查詢
- 批次 callback
- 批次錯誤隔離
- 批次輸出檔寫入
- 非同步批次翻譯
- 重用 Stage-07.2 SDK Translation API，不複製 Runtime 邏輯

測試指令
--------
python tests\beta_stage_07_3\launcher_sdk_batch_api_test.py
python tests\beta_stage_07_2\launcher_sdk_translation_api_test.py
python tests\beta_stage_07_1\launcher_sdk_session_api_test.py
python tests\beta_stage_07_0\launcher_sdk_core_test.py
python tests\beta_stage_06_9\launcher_cli_freeze_test.py
python tests\foundation_09\launcher_foundation_freeze_test.py

Git Commit 建議
---------------
git add sdk tests\beta_stage_07_3 README_NTPE_1_0_Beta_Stage_07_3.txt
git commit -m "Stage-07.3 SDK Batch API"
git push origin main
git tag beta-stage-07.3-sdk-batch-api
git push origin beta-stage-07.3-sdk-batch-api
