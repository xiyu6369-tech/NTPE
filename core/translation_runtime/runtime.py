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
from core.ai_provider import (
    AIProvider,
    ProviderConfigLayer,
    ProviderManager,
    ProviderRequest,
    ProviderRouter,
    RuntimeProviderBridge,
    build_standard_provider_registry,
)


class TranslationRuntime:
    """
    NTPE 1.2 Professional formal Translation Runtime facade.

    This layer is intentionally additive: it keeps NTPE 1.1 LTS APIs intact while
    making launcher, TXT, and batch translation share one official runtime entry.
    """

    version = "1.2-professional-stage-14.2"

    def __init__(self, root: str | Path | None = None, api_key: str | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2]
        self.api_key = api_key
        self.engine = TranslationEngine(root=self.root, api_key=api_key)
        self.provider = RuntimeProviderAdapter(self.engine, RuntimeProviderPolicy())
        self.ai_provider_config = ProviderConfigLayer.load(self.root / "config" / "provider_config.json")
        self.ai_provider_manager = ProviderManager(
            registry=self.ai_provider_config.build_registry(),
            router=ProviderRouter(default_provider=self.ai_provider_config.default_provider),
            config_layer=self.ai_provider_config,
        )
        self.ai_provider_bridge = RuntimeProviderBridge(self.ai_provider_manager)
        self.qa_policy = RuntimeQAPolicy()
        self.sessions = TranslationSessionManager(self.root, self)
        self.pipelines = TranslationPipelineManager(self.root, self)
        self.resources = TranslationResourceManager(self.root)
        self.plugins = TranslationPluginManager(self.root)
        self.plugin_runtime = TranslationPluginRuntime(self.root, self.plugins)

        # Series context stores (set by SeriesTranslationCoordinator for series-aware execution)
        self._series_registry: Any = None
        self._series_memory_store: Any = None
        self._series_entity_registry: Any = None
        self._series_glossary: Any = None
        self._series_knowledge: Any = None
        self._series_checkpoint_manager: Any = None

        # Series context injected by coordinator
        self._series_context: Any = None
        self._series_book_memory_store: Any = None
        self._series_book_context_store: Any = None
        self._series_user_overrides: Any = None
        self._series_locked_dictionary: Any = None
        self._series_alias_map: Any = None
        self._series_hydration_summary: Any = None
        self._series_entity_hydration_report: Any = None
        self._last_entity_resolver_overrides: Any = None



    def bind_ai_provider_manager(self, manager: ProviderManager) -> dict[str, Any]:
        """Bind an AI ProviderManager to Translation Runtime without replacing LTS provider paths."""
        self.ai_provider_manager = manager
        self.ai_provider_bridge = RuntimeProviderBridge(manager)
        self.ai_provider_config = manager.config_layer or self.ai_provider_config
        return {"status": "success", "default_provider": manager.registry.default_name(), "providers": manager.registry.list()}

    def register_ai_provider(self, provider: AIProvider, default: bool = False) -> dict[str, Any]:
        self.ai_provider_manager.registry.register(provider, default=default)
        return {"status": "success", "provider": provider.name, "default_provider": self.ai_provider_manager.registry.default_name()}

    def complete_provider_prompt(self, prompt: str, model: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.ai_provider_bridge.execute_prompt(prompt=prompt, model=model, metadata=metadata or {})
        return response.to_dict() if hasattr(response, "to_dict") else dict(response)

    def stream_provider_prompt(self, prompt: str, model: str | None = None, metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        chunks = self.ai_provider_bridge.stream_prompt(prompt=prompt, model=model, metadata=metadata or {})
        return [
            {
                "text": chunk.text,
                "provider": chunk.provider,
                "model": chunk.model,
                "index": chunk.index,
                "done": chunk.done,
                "metadata": dict(chunk.metadata),
            }
            for chunk in chunks
        ]

    def discover_provider_models(self, provider: str | None = None) -> dict[str, Any]:
        models = self.ai_provider_bridge.discover_models(provider)
        return {"status": "success", "provider": provider, "models": [model.to_dict() for model in models]}

    def detect_provider_capabilities(self, provider: str | None = None) -> dict[str, Any]:
        capabilities = self.ai_provider_bridge.detect_capabilities(provider)
        return {"status": "success", "capabilities": {name: cap.to_dict() for name, cap in capabilities.items()}}

    def provider_health_check(self) -> dict[str, Any]:
        return {"status": "success", "health": self.ai_provider_bridge.health_check()}

    def provider_manifest(self) -> dict[str, Any]:
        return self.ai_provider_manager.manifest()

    def provider_config_manifest(self) -> dict[str, Any]:
        return {"status": "success", "config": self.ai_provider_config.manifest()}

    def validate_provider_credentials(self) -> dict[str, Any]:
        return {"status": "success", "credentials": self.ai_provider_config.validate_credentials()}

    def save_provider_config_template(self, path: str | Path | None = None) -> dict[str, Any]:
        target = Path(path) if path else self.root / "config" / "provider_config.template.json"
        saved = self.ai_provider_config.save_template(target)
        return {"status": "success", "path": str(saved)}

    def set_series_context(
        self,
        series_registry: Any,
        series_memory_store: Any,
        series_entity_registry: Any,
        series_glossary: Any,
        series_knowledge: Any,
        series_checkpoint_manager: Any,
    ) -> None:
        """Set series stores for series-aware translation (called by SeriesTranslationCoordinator)."""
        self._series_registry = series_registry
        self._series_memory_store = series_memory_store
        self._series_entity_registry = series_entity_registry
        self._series_glossary = series_glossary
        self._series_knowledge = series_knowledge
        self._series_checkpoint_manager = series_checkpoint_manager

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
        return self.ai_provider_bridge.attach_runtime_manifest(build_runtime_contract(self.version, self.root).to_dict())

    def validate_compatibility(self) -> dict[str, Any]:
        """Verify that the public runtime surface remains backward compatible."""
        return validate_runtime_contract(self)

    def translate_package_file(self, package_path: str | Path) -> dict[str, Any]:
        return self.provider.translate_package_file(package_path)

    def translate_package(
    self,
    package: dict,
    package_path: str | Path | None = None,
    series_id: str | None = None,
    book_identity: str | None = None,
) -> dict[str, Any]:
        # If series context is provided, inject it before translation
        if series_id and book_identity:
            if self._series_context is None:
                from core.series_orchestration.runtime_integration import build_series_context, inject_series_context

                series_context = build_series_context(
                    series_id=series_id,
                    book_identity=book_identity,
                    output_root=self.root,
                    series_registry=self._series_registry,
                    series_memory_store=self._series_memory_store,
                    series_entity_registry=self._series_entity_registry,
                    series_glossary=self._series_glossary,
                    series_knowledge=self._series_knowledge,
                    series_checkpoint_manager=self._series_checkpoint_manager,
                )
                inject_series_context(
                    runtime=self,
                    series_context=series_context,
                    output_root=self.root,
                    series_memory_store=self._series_memory_store,
                    series_entity_registry=self._series_entity_registry,
                    series_glossary=self._series_glossary,
                    series_knowledge=self._series_knowledge,
                    series_registry=self._series_registry,
                    book_identity=book_identity,
                )

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

    def translate_txt(
    self,
    options: Any,
    series_id: str | None = None,
    book_identity: str | None = None,
) -> dict[str, Any]:
        # Lazy import prevents circular imports and preserves the frozen LTS module.
        from lts.txt_translation_runtime import translate_txt

        # If series context is provided, inject it before translation
        if series_id and book_identity:
            if self._series_context is None:
                # Build series context on-demand if not already injected by coordinator
                from core.series_orchestration.runtime_integration import build_series_context, inject_series_context

                series_context = build_series_context(
                    series_id=series_id,
                    book_identity=book_identity,
                    output_root=self.root,
                    series_registry=self._series_registry,
                    series_memory_store=self._series_memory_store,
                    series_entity_registry=self._series_entity_registry,
                    series_glossary=self._series_glossary,
                    series_knowledge=self._series_knowledge,
                    series_checkpoint_manager=self._series_checkpoint_manager,
                )
                inject_series_context(
                    runtime=self,
                    series_context=series_context,
                    output_root=self.root,
                    series_memory_store=self._series_memory_store,
                    series_entity_registry=self._series_entity_registry,
                    series_glossary=self._series_glossary,
                    series_knowledge=self._series_knowledge,
                    series_registry=self._series_registry,
                    book_identity=book_identity,
                )

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
