Foundation-08.4 Knowledge Cache
================================

新增 Knowledge Cache 層，提供 Repository Query Cache、Domain Context Cache、Snapshot Cache、LRU / TTL policy、Cache Invalidation、Runtime Cache Integration、Cache Metrics 與 Event Bus Cache events。

新增檔案：
- core/knowledge/cache/__init__.py
- core/knowledge/cache/cache_manager.py
- core/knowledge/cache/cache_policy.py
- core/knowledge/cache/cache_runtime.py
- core/knowledge/cache/cache_snapshot.py
- core/knowledge/cache/cache_store.py
- core/knowledge/cache/manifest.py
- tests/foundation_08_4/launcher_knowledge_cache_test.py

修改檔案：
- core/knowledge/__init__.py

執行：
cd /d D:\Python\NTPE
python tests\foundation_08_4\launcher_knowledge_cache_test.py

Commit：
feat(foundation-08.4): add knowledge cache layer
