NTPE Foundation-07.2 Intelligence Runtime Integration
====================================================

Purpose
-------
Foundation-07.2 connects the Foundation-07.1 Translation Intelligence Engine to
runtime execution with pre/post segment hooks. This update is additive and keeps
Foundation-07.0 contracts and Foundation-07.1 engine behavior backward compatible.

Added files
-----------
core/intelligence/runtime_integration.py
tests/foundation_07_2/launcher_translation_intelligence_runtime_integration_test.py

Modified file
-------------
core/intelligence/__init__.py

Test command
------------
cd /d D:\Python\NTPE
python tests\foundation_07_2\launcher_translation_intelligence_runtime_integration_test.py

Expected result
---------------
Before Segment                    PASS
Prompt Context Attached           PASS
Runtime Manifest Attached         PASS
Integration Manifest              PASS
Metadata Merged                   PASS
After Segment                     PASS
Consistency Passed                PASS
After Snapshot                    PASS
Consistency Issues                PASS
Process Runtime Segment           PASS
Process Consistency               PASS
Runtime Payload                   PASS
Payload Prompt Package            PASS
Object Segment                    PASS
Wrapped Executor                  PASS
Wrapped Consistency               PASS
Backward Engine                   PASS
Backward Store                    PASS
PASS

Suggested commit
----------------
feat(foundation-07.2): integrate intelligence engine with runtime flow
