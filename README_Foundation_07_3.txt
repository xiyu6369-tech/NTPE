NTPE Foundation-07.3 Intelligence Lifecycle
===========================================

This is an additive update on top of Foundation-07.0, 07.1, and 07.2.
It adds lifecycle management for Translation Intelligence without changing the
existing contract, engine, or runtime integration behavior.

Added modules:
- core/intelligence/lifecycle.py
- core/intelligence/snapshot_manager.py
- core/intelligence/versioning.py
- core/intelligence/merge_strategy.py
- core/intelligence/persistence_contract.py
- core/intelligence/session_scope.py

Updated:
- core/intelligence/__init__.py

Install:
Copy/merge this package into the NTPE project root:
D:\Python\NTPE

Test:
python tests\foundation_07_3\launcher_translation_intelligence_lifecycle_test.py

Suggested commit:
feat(foundation-07.3): add intelligence lifecycle management
