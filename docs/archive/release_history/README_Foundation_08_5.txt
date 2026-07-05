Foundation-08.5 Knowledge Query API
===================================

新增 Knowledge Layer 對外查詢 API，提供 Runtime、Prompt Pipeline、Plugin、未來 CLI/SDK 共用的統一知識查詢入口。

新增內容：
- core/knowledge/api/__init__.py
- core/knowledge/api/knowledge_api.py
- core/knowledge/api/query_builder.py
- core/knowledge/api/query_executor.py
- core/knowledge/api/filters.py
- core/knowledge/api/pagination.py
- core/knowledge/api/manifest.py
- tests/foundation_08_5/launcher_knowledge_query_api_test.py

修改內容：
- core/knowledge/__init__.py：新增 Foundation-08.5 public exports。

測試：
python tests\foundation_08_5\launcher_knowledge_query_api_test.py

Commit 建議：
feat(foundation-08.5): add knowledge query api
