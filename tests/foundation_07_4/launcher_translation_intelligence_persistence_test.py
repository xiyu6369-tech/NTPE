import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.intelligence import (
    IntelligencePersistenceLoader,
    IntelligencePersistenceRegistry,
    IntelligenceSessionScope,
    IntelligenceSnapshotSerializer,
    JsonIntelligenceStore,
    SQLiteIntelligenceStore,
    TranslationIntelligenceLifecycle,
    get_default_persistence_registry,
)


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{name:<34} {status}")
    if not condition:
        raise AssertionError(name)


def main():
    tmp = tempfile.mkdtemp(prefix="ntpe_07_4_")
    try:
        sample = {
            "characters": {"鄭泰義": {"name": "鄭泰義", "aliases": ["정태의"]}},
            "glossary": {"정태의": "鄭泰義"},
            "manifest": {"source": "foundation-07.4-test"},
        }

        serializer = IntelligenceSnapshotSerializer()
        payload = serializer.dumps(sample)
        restored = serializer.loads(payload)
        check("Snapshot Serialize", isinstance(payload, str) and "鄭泰義" in payload)
        check("Snapshot Deserialize", restored["characters"]["鄭泰義"]["aliases"] == ["정태의"])

        json_dir = os.path.join(tmp, "json")
        json_store = JsonIntelligenceStore(json_dir)
        saved_json = json_store.save_snapshot("job:test/session:json", sample)
        loaded_json = json_store.load_snapshot("job:test/session:json")
        check("JSON Store", loaded_json is not None and loaded_json["glossary"]["정태의"] == "鄭泰義")
        check("JSON List", len(json_store.list_scope_keys()) == 1)
        check("JSON Delete", json_store.delete_snapshot("job:test/session:json") is True)

        sqlite_path = os.path.join(tmp, "store.sqlite3")
        sqlite_store = SQLiteIntelligenceStore(sqlite_path)
        sqlite_store.save_snapshot("job:test/session:sqlite", sample)
        loaded_sqlite = sqlite_store.load_snapshot("job:test/session:sqlite")
        check("SQLite Store", loaded_sqlite is not None and loaded_sqlite["characters"]["鄭泰義"]["name"] == "鄭泰義")
        check("SQLite List", sqlite_store.list_scope_keys() == ["job:test/session:sqlite"])
        check("SQLite Delete", sqlite_store.delete_snapshot("job:test/session:sqlite") is True)

        registry = IntelligencePersistenceRegistry()
        registry_json = registry.create("json", root_dir=os.path.join(tmp, "registry_json"))
        registry_sqlite = registry.create("sqlite", db_path=os.path.join(tmp, "registry.sqlite3"))
        check("Registry Switch", isinstance(registry_json, JsonIntelligenceStore) and isinstance(registry_sqlite, SQLiteIntelligenceStore))
        check("Default Registry", "json" in get_default_persistence_registry().names() and "sqlite" in get_default_persistence_registry().names())

        scope = IntelligenceSessionScope(job_id="job-074", runtime_id="runtime-074", session_id="session-074")
        lifecycle_store = JsonIntelligenceStore(os.path.join(tmp, "lifecycle"))
        lifecycle = TranslationIntelligenceLifecycle(scope=scope, persistence=lifecycle_store)
        lifecycle.after_segment(
            segment_id="seg-001",
            source_text="정태의는 방에 들어갔다.",
            output_text="鄭泰義走進房間。",
            metadata={"chapter": 1},
        )
        loaded_runtime = lifecycle_store.load_snapshot(scope.key())
        check("Runtime Restore", loaded_runtime is not None and loaded_runtime.get("manifest", {}).get("scope", {}).get("job_id") == "job-074")

        loader = IntelligencePersistenceLoader(lifecycle_store)
        restored_lifecycle = loader.restore_lifecycle(scope=scope)
        check("Session Restore", restored_lifecycle.active_snapshot is not None and restored_lifecycle.scope.key() == scope.key())

        segment_keys = lifecycle_store.list_scope_keys()
        check("Segment Persisted", any("seg-001" in key for key in segment_keys))

        direct_loader_store = loader.build_store("sqlite", db_path=os.path.join(tmp, "loader.sqlite3"))
        check("Loader Build Store", isinstance(direct_loader_store, SQLiteIntelligenceStore))

        check("Backward Compatible", hasattr(json_store, "save_snapshot") and hasattr(sqlite_store, "load_snapshot"))
        print("PASS")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
