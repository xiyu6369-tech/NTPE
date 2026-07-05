NTPE 1.0 Beta - Stage-11.7 Runtime Middleware

新增內容
--------
- runtime_api/runtime_middleware.py
- runtime_api/middleware_request.py
- runtime_api/middleware_response.py
- runtime_api/middleware_api.py
- tests/beta_stage_11_7/

目標
----
建立 Runtime API 的可選 Middleware 層，支援 request before hook、response after hook、error hook、priority ordering、enable / disable、summary 與 middleware.execute facade。

相容性
------
本 Stage 僅新增 runtime_api middleware 模組，不修改 Foundation、CLI、SDK、Integration、Workflow、Platform Services，也不改變既有 RuntimeApi.execute 行為。

測試
----
python tests/beta_stage_11_7/launcher_runtime_middleware_test.py
python tests/beta_stage_11_7/runtime_middleware_test.py
python tests/beta_stage_11_7/compatibility_test.py

結果
----
PASS
