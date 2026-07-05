from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

from core.translation_engine.translation_engine import TranslationEngine
from .runtime_contract import build_runtime_contract, validate_runtime_contract
from .runtime_provider import RuntimeProviderAdapter, RuntimeProviderPolicy
from .runtime_qa import RuntimeQAPolicy, analyze_runtime_quality
from .runtime_recovery import RuntimeCheckpointKey, mark_checkpoint_completed, recovery_summary, update_checkpoint
from core.translation_session import TranslationSessionManager
from core.translation_pipeline import TranslationPipelineManager
from core.translation_resources import TranslationResourceManager
from core.translation_plugins import TranslationPluginManager, TranslationPluginRuntime


class TranslationRuntime:
    """
    NTPE 1.2 Professional formal Translation Runtime facade.

    This layer is intentionally additive: it keeps NTPE 1.1 LTS APIs intact while
    making launcher, TXT, and batch translation share one official runtime entry.
    """

    version = "1.2-professional-stage-09"

    def __init__(self, root: str | Path | None = None, api_key: str | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2]
        self.api_key = api_key
        self.engine = TranslationEngine(root=self.root, api_key=api_key)
        self.provider = RuntimeProviderAdapter(self.engine, RuntimeProviderPolicy())
        self.qa_policy = RuntimeQAPolicy()
        self.sessions = TranslationSessionManager(self.root, self)
        self.pipelines = TranslationPipelineManager(self.root, self)
        self.resources = TranslationResourceManager(self.root)
        self.plugins = TranslationPluginManager(self.root)
        self.plugin_runtime = TranslationPluginRuntime(self.root, self.plugins)


    def describe_plugin_runtime(self) -> dict[str, Any]:
        return self.plugin_runtime.describe()

    def validate_plugin_runtime(self) -> dict[str, Any]:
        return self.plugin_runtime.validate()

    def execute_pipeline_with_plugins(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.plugin_runtime.execute_pipeline(self.pipelines, payload=payload)

    def describe_plugins(self) -> dict[str, Any]:
        return self.plugins.describe()

    def validate_plugins(self) -> dict[str, Any]:
        return self.plugins.validate()

    def save_plugin_manifest(self, manifest_id: str | None = None) -> dict[str, Any]:
        return self.plugins.save_manifest(manifest_id=manifest_id)

    def get_plugin(self, kind: str, name: str = "default") -> dict[str, Any] | None:
        return self.plugins.get(kind, name)

    def execute_plugin(self, kind: str, name: str = "default", payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.plugins.execute(kind=kind, name=name, payload=payload, metadata=metadata)

    def execute_plugin_chain(self, kinds: list[str] | tuple[str, ...] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.plugins.execute_chain(kinds=kinds, payload=payload)

    def describe_resources(self) -> dict[str, Any]:
        return self.resources.describe()

    def validate_resources(self) -> dict[str, Any]:
        return self.resources.validate()

    def save_resource_manifest(self, manifest_id: str | None = None) -> dict[str, Any]:
        return self.resources.save_manifest(manifest_id=manifest_id)

    def get_resource(self, kind: str, name: str = "default") -> dict[str, Any] | None:
        resource = self.resources.get(kind, name)
        return resource.to_dict() if resource else None

    def describe_pipeline(self) -> dict[str, Any]:
        return self.pipelines.describe()

    def validate_pipeline(self) -> dict[str, Any]:
        return self.pipelines.validate()

    def execute_pipeline(self, payload: dict[str, Any] | None = None, handlers: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.pipelines.execute(payload=payload, handlers=handlers)

    def save_pipeline_manifest(self, pipeline_id: str | None = None) -> dict[str, Any]:
        return self.pipelines.save_manifest(pipeline_id=pipeline_id)

    def create_session(self, mode: str = "runtime", input_source: str = "", output_target: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        session = self.sessions.create_session(mode=mode, input_source=input_source, output_target=output_target, metadata=metadata)
        return {"status": "success", "session_id": session.session_id, "manifest": session.manifest().to_dict()}

    def list_sessions(self) -> dict[str, Any]:
        return self.sessions.list_sessions()

    def translate_package_file_session(self, package_path: str | Path) -> dict[str, Any]:
        session = self.sessions.create_session(mode="package", input_source=str(package_path))
        return session.execute(lambda: self.translate_package_file(package_path))


    def describe(self) -> dict[str, Any]:
        """Return the formal runtime contract for diagnostics and future SDK/UI layers."""
        return build_runtime_contract(self.version, self.root).to_dict()

    def validate_compatibility(self) -> dict[str, Any]:
        """Verify that the public runtime surface remains backward compatible."""
        return validate_runtime_contract(self)

    def translate_package_file(self, package_path: str | Path) -> dict[str, Any]:
        return self.provider.translate_package_file(package_path)

    def translate_package(self, package: dict, package_path: str | Path | None = None) -> dict[str, Any]:
        return self.provider.translate_package(package, package_path=package_path)

    def analyze_quality(self, source_text: str, translated_text: str, policy: RuntimeQAPolicy | None = None) -> dict[str, Any]:
        return analyze_runtime_quality(source_text, translated_text, policy or self.qa_policy)

    def checkpoint(self, scope: str, name: str, **cursor: Any) -> dict[str, Any]:
        key = RuntimeCheckpointKey(scope=scope, name=name)
        checkpoint = update_checkpoint(self.root, key, status="running", cursor=cursor)
        return checkpoint.to_dict()

    def checkpoint_error(self, scope: str, name: str, error: str, **cursor: Any) -> dict[str, Any]:
        key = RuntimeCheckpointKey(scope=scope, name=name)
        checkpoint = update_checkpoint(self.root, key, status="failed", cursor=cursor, error={"message": error})
        return checkpoint.to_dict()

    def checkpoint_completed(self, scope: str, name: str, **metadata: Any) -> dict[str, Any]:
        key = RuntimeCheckpointKey(scope=scope, name=name)
        checkpoint = mark_checkpoint_completed(self.root, key, metadata=metadata)
        return checkpoint.to_dict()

    def recovery_summary(self) -> dict[str, Any]:
        return recovery_summary(self.root)

    def translate_txt(self, options: Any) -> dict[str, Any]:
        # Lazy import prevents circular imports and preserves the frozen LTS module.
        from lts.txt_translation_runtime import translate_txt
        return translate_txt(options, root=self.root)

    def translate_batch(self, options: Any) -> dict[str, Any]:
        from lts.batch_translation_runtime import translate_batch
        return translate_batch(options, root=self.root)

    def main_txt(self, argv: Iterable[str] | None = None) -> int:
        from lts.txt_translation_runtime import parse_args
        options = parse_args(argv)
        result = self.translate_txt(options)
        print("NTPE 1.2 Professional TXT Translation Runtime")
        print("=============================================")
        print(f"status: {result['status']}")
        print(f"input: {result.get('input', '')}")
        print(f"output: {result.get('output', '')}")
        print(f"chunks: {result.get('chunk_total', 0)}")
        print(f"resume_state: {result.get('resume_state', '')}")
        return 0 if result.get("status") == "success" else 1

    def main_batch(self, argv: Iterable[str] | None = None) -> int:
        from lts.batch_translation_runtime import parse_args
        options = parse_args(argv)
        result = self.translate_batch(options)
        print("NTPE 1.2 Professional Batch Translation Runtime")
        print("================================================")
        print(f"status: {result['status']}")
        print(f"input_dir: {result.get('input_dir', '')}")
        print(f"output_dir: {result.get('output_dir', '')}")
        summary = result.get("summary", {})
        print(f"files: {summary.get('total_files', 0)}")
        print(f"success: {summary.get('success', 0)}")
        print(f"failed: {summary.get('failed', 0)}")
        return 0 if result.get("status") == "success" else 1


def main_txt(argv: Iterable[str] | None = None) -> int:
    return TranslationRuntime().main_txt(argv)


def main_batch(argv: Iterable[str] | None = None) -> int:
    return TranslationRuntime().main_batch(argv)
