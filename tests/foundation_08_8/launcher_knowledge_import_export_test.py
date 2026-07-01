import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    InMemoryKnowledgeRepository,
    KnowledgeExporter,
    KnowledgeImporter,
    KnowledgeItem,
    KnowledgePackageBuilder,
    KnowledgePackageReader,
    KnowledgePackageValidator,
    KnowledgeQuery,
    KnowledgeSnapshot,
    build_knowledge_io_manifest,
)


def report(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main():
    repo = InMemoryKnowledgeRepository(metadata={"test": "08.8"})
    repo.put(KnowledgeItem(key="Jeong Taeui", value="鄭泰義", domain="character", metadata={"role": "lead"}))
    repo.put(KnowledgeItem(key="Ilay", value="伊萊", domain="character"))
    repo.put(KnowledgeItem(key="UNHRDO", value="聯合國人力資源開發機構", domain="glossary"))
    repo.put(KnowledgeItem(key="island", value="南國島嶼", domain="scene"))

    builder = KnowledgePackageBuilder(repository=repo, metadata={"project": "NTPE"})
    package = builder.build(name="chapter-package", domains=["character", "glossary"])
    report("Package Builder", package["manifest"]["item_count"] == 3 and package["manifest"]["schema"])

    validator = KnowledgePackageValidator()
    validation = validator.validate(package)
    report("Package Validation", validation.valid and not validation.errors)
    report("Version Compatible", validator.compatible(package))

    reader = KnowledgePackageReader(validator)
    items = reader.items(package)
    report("Package Reader", len(items) == 3 and items[0].domain in {"character", "glossary"})

    snapshot = repo.snapshot("chapter-snapshot")
    snapshot_package = builder.build_from_snapshot(snapshot)
    report("Snapshot Package", snapshot_package["manifest"]["snapshot_count"] == 1)

    exporter = KnowledgeExporter(repository=repo, metadata={"exporter": "test"})
    export_package = exporter.package(name="full-package", snapshots=[snapshot])
    report("Knowledge Exporter", export_package["manifest"]["item_count"] == 4 and export_package["manifest"]["snapshot_count"] == 1)

    with tempfile.TemporaryDirectory() as tempdir:
        json_path = os.path.join(tempdir, "knowledge.json")
        zip_path = os.path.join(tempdir, "knowledge.zip")
        snapshot_path = os.path.join(tempdir, "snapshot.zip")

        exporter.export_json(json_path, package=export_package)
        loaded_json = reader.read_json(json_path)
        report("JSON Export", os.path.exists(json_path) and loaded_json["manifest"]["name"] == "full-package")

        target = InMemoryKnowledgeRepository()
        importer = KnowledgeImporter(target)
        result = importer.import_json(json_path)
        report("JSON Import", result["imported"] == 4 and target.get("Jeong Taeui", "character").value == "鄭泰義")

        exporter.export_zip(zip_path, package=export_package)
        loaded_zip = reader.read_zip(zip_path)
        report("ZIP Export", os.path.exists(zip_path) and loaded_zip["manifest"]["item_count"] == 4)

        target_zip = InMemoryKnowledgeRepository()
        zip_importer = KnowledgeImporter(target_zip)
        zip_result = zip_importer.import_zip(zip_path)
        report("ZIP Import", zip_result["imported"] == 4 and target_zip.get("UNHRDO", "glossary") is not None)

        exporter.export_snapshot_package(snapshot, snapshot_path)
        snapshot_loaded = reader.read_zip(snapshot_path)
        report("Snapshot Export", snapshot_loaded["manifest"]["snapshot_count"] == 1)

        snapshot_target = InMemoryKnowledgeRepository()
        snapshot_importer = KnowledgeImporter(snapshot_target)
        snapshot_result = snapshot_importer.import_snapshot(KnowledgeSnapshot.from_dict(snapshot_loaded["snapshots"][0]))
        report("Snapshot Import", snapshot_result["imported"] == 4 and snapshot_target.get("island", "scene") is not None)

    migration_source = exporter.package(name="migration", domains=["character", "scene"])
    migration_target = InMemoryKnowledgeRepository()
    migration_result = KnowledgeImporter(migration_target).import_package(migration_source)
    report("Project Migration", migration_result["imported"] == 3 and len(migration_target.query(KnowledgeQuery(domain="character"))) == 2)

    invalid = {"manifest": {"schema": "ntpe.knowledge.package.v1", "version": "foundation-08.8"}, "items": [{"domain": "character"}], "snapshots": []}
    report("Validation Failure", not validator.validate(invalid).valid)

    manifest = build_knowledge_io_manifest(extra="ok")
    report("Manifest IO", "export_zip" in manifest["capabilities"] and manifest["metadata"]["extra"] == "ok")

    # import with merge=False clears old repository through the public contract.
    replace_repo = InMemoryKnowledgeRepository([KnowledgeItem(key="old", value="舊", domain="character")])
    replace_result = KnowledgeImporter(replace_repo).import_package(package, merge=False)
    report("Replace Import", replace_result["imported"] == 3 and replace_repo.get("old", "character") is None)

    report("Query Compatible", len(repo.query(KnowledgeQuery(text="鄭泰義"))) == 1)
    report("Backward Compatible", repo.get("Jeong Taeui", "character").value == "鄭泰義")
    print("PASS")


if __name__ == "__main__":
    main()
