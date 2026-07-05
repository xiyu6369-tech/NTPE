NTPE Foundation-08.7 Knowledge Snapshot Manager
================================================

新增內容：
- core/knowledge/snapshot/
  - snapshot_manager.py
  - snapshot_registry.py
  - snapshot_serializer.py
  - snapshot_history.py
  - snapshot_diff.py
  - manifest.py
- tests/foundation_08_7/launcher_knowledge_snapshot_manager_test.py

能力：
- Snapshot Manager
- Snapshot Registry
- Snapshot History
- Snapshot Diff
- Snapshot Merge
- Snapshot Rollback
- Snapshot Export / Import
- Runtime Snapshot Control
- Event Bus Snapshot Hook
- Backward Compatible with Foundation-08.0 ~ 08.6

測試：
cd /d D:\Python\NTPE
python tests\foundation_08_7\launcher_knowledge_snapshot_manager_test.py

Commit 建議：
feat(foundation-08.7): add knowledge snapshot manager
