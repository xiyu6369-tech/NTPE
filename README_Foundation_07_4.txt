Foundation-07.4 Intelligence Persistence
=======================================

Purpose
-------
Adds durable persistence implementations for the Foundation-07 Intelligence Lifecycle.

Added files
-----------
core/intelligence/persistence/__init__.py
core/intelligence/persistence/serializer.py
core/intelligence/persistence/json_store.py
core/intelligence/persistence/sqlite_store.py
core/intelligence/persistence/registry.py
core/intelligence/persistence/loader.py
tests/foundation_07_4/launcher_translation_intelligence_persistence_test.py

Updated file
------------
core/intelligence/__init__.py

Run test
--------
cd /d D:\Python\NTPE
python tests\foundation_07_4\launcher_translation_intelligence_persistence_test.py

Commit
------
feat(foundation-07.4): add intelligence persistence stores
