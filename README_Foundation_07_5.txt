NTPE Foundation-07.5 Intelligence Event Bus
==========================================

Purpose
-------
Adds a dependency-free in-process event bus for Translation Intelligence.
This is an incremental update and is backward compatible with Foundation-07.0 to 07.4.

Added files
-----------
core/intelligence/events/__init__.py
core/intelligence/events/event.py
core/intelligence/events/event_bus.py
core/intelligence/events/publisher.py
core/intelligence/events/subscriber.py
core/intelligence/events/dispatcher.py
core/intelligence/events/runtime_events.py
tests/foundation_07_5/launcher_translation_intelligence_event_bus_test.py

Modified files
--------------
core/intelligence/__init__.py

Run test
--------
cd /d D:\Python\NTPE
python tests\foundation_07_5\launcher_translation_intelligence_event_bus_test.py

Commit suggestion
-----------------
feat(foundation-07.5): add intelligence event bus
