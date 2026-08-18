"""RM-6.4.0 Runtime Orchestrator.

Coordinates Knowledge Runtime → Prompt Runtime → Translation Runtime
→ Runtime Session → Checkpoint → Trace → Translation Engine end-to-end.

Orchestrator is a coordination layer, NOT a reimplementation.
All components remain unmodified. Orchestrator only calls, sequences,
and assembles their public interfaces.

Architecture:
    Translation Input
            │
            ▼
    RuntimeOrchestrator
            │
            ├── KnowledgeRuntimeManager
            ├── PromptBuilder
            ├── TranslationRuntimeAdapter
            ├── RuntimeSessionManager
            ├── RuntimeCheckpointManager
            ├── RuntimeTraceCollector
            └── TranslationEngine
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.knowledge_runtime import KnowledgeBundle, KnowledgeRuntimeManager
from core.prompt_runtime import PromptBuilder
from core.translation_runtime import TranslationRuntimeAdapter
from core.runtime_session import RuntimeSessionManager, RunStatus, TranslationSession
from core.runtime_checkpoint import RuntimeCheckpointManager
from core.runtime_trace import RuntimeTraceCollector, EventType
from core.entity_resolver import EntityExtractor, EntityResolver, build_known_entities_from_runtime
from core.character_memory_v2 import (
    MemoryStore,
    select_prompt_eligible_memories,
    load_character_memory,
    save_character_memory,
)
from core.context_scene_memory import (
    ContextMemoryStore,
    select_context_for_translation,
    load_context_memory,
    save_context_memory,
)
from core.runtime_orchestrator.models import (
    RuntimeExecutionContext,
    RuntimeExecutionResult,
    utc_now_iso,
)


class RuntimeOrchestrator:
    """High-level entry point for the Runtime Layer.

    Orchestrates the full translation pipeline across all RM-6
    runtime components. Owns ordering, invocation, and assembly.
    Does NOT modify prompts, translations, or provider requests.
    """

    version = "rm-6.4.0"

    def __init__(self):
        self.knowledge = KnowledgeRuntimeManager()
        self._builder: Optional[PromptBuilder] = None
        self._adapter = TranslationRuntimeAdapter()
        self._session_mgr = RuntimeSessionManager()
        self._checkpoint_mgr = RuntimeCheckpointManager()
        self._trace: Optional[RuntimeTraceCollector] = None
        self._engine: Optional[Any] = None

    def set_engine(self, engine: Any) -> None:
        self._engine = engine

    def set_api_key(self, api_key: str) -> None:
        if self._engine is not None:
            self._engine.api_key = api_key

    def build_context(
        self,
        session_id: str = "",
        snapshot_id: str = "",
        prompt_hash: str = "",
        request_hash: str = "",
        current_chunk: int = 0,
        total_chunks: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeExecutionContext:
        return RuntimeExecutionContext(
            session_id=session_id,
            snapshot_id=snapshot_id,
            prompt_hash=prompt_hash,
            request_hash=request_hash,
            current_chunk=current_chunk,
            total_chunks=total_chunks,
            metadata=dict(metadata or {}),
        )

    def start_session(
        self,
        snapshot_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranslationSession:
        session = self._session_mgr.create_session(
            snapshot_id=snapshot_id,
            metadata=dict(metadata or {}),
        )
        self._trace = RuntimeTraceCollector(session_id=session.session_id)
        self._trace = self._trace.record_event(
            EventType.SESSION_CREATED,
            metadata={"session_id": session.session_id},
        )
        return session

    def prepare_request(
        self,
        chunk_text: str = "",
        session_id: str = "",
        snapshot_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        bundles = self.knowledge.load_all(metadata=metadata)
        bundle_list = list(bundles.values())
        merged = self.knowledge.build_merged_runtime(bundles=bundle_list)

        builder = PromptBuilder(chunk_text=chunk_text)
        assembly = builder.build(merged)

        request = self._adapter.prepare(
            assembly,
            snapshot_id=snapshot_id,
            metadata=dict(metadata or {}),
        )
        self._session_mgr.save_session(
            TranslationSession(
                session_id=session_id or "",
                snapshot_id=snapshot_id,
                prompt_hash=request.prompt_hash,
                metadata=dict(metadata or {}),
            )
        )
        return {
            "prompt": request.prompt,
            "prompt_hash": request.prompt_hash,
            "snapshot_id": request.snapshot_id,
            "section_count": request.section_count,
            "token_count": request.token_count,
            "metadata": dict(request.metadata),
            "runtime_snapshot": dict(request.runtime_snapshot),
        }

    def execute(
        self,
        chunk_text: str = "",
        session_id: str = "",
        snapshot_id: str = "",
        current_chunk: int = 0,
        total_chunks: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        engine_kwargs: Optional[Dict[str, Any]] = None,
    ) -> RuntimeExecutionResult:
        metadata = dict(metadata or {})
        engine_kwargs = dict(engine_kwargs or {})

        # Extract RM-8.2 extensions (feature-gated)
        enable_cross_chunk_context = metadata.pop("enable_cross_chunk_context", False)
        context_selection = metadata.pop("context_selection", None) if enable_cross_chunk_context else None
        scene_state = metadata.pop("scene_state", None) if enable_cross_chunk_context else None
        narrative_state = metadata.pop("narrative_state", None) if enable_cross_chunk_context else None
        entity_injection_set = metadata.pop("entity_injection_set", None)

        # Extract character memory store (if provided)
        character_memory_store = metadata.pop("character_memory_store", None)
        character_memory_scope = metadata.pop("character_memory_scope", None) or {}

        # Extract context/scene memory store (if provided)
        context_memory_store = metadata.pop("context_memory_store", None)
        context_memory_scope = metadata.pop("context_memory_scope", None) or {}

        # 1. Knowledge Runtime → MergedRuntime
        bundled_entries = self.knowledge.load_all()
        bundle_list = list(bundled_entries.values())
        merged = self.knowledge.build_merged_runtime(bundles=bundle_list)

        # 1b. Entity Resolver — per-chunk resolution (RM-7.2)
        known_entities = build_known_entities_from_runtime(merged)
        extractor = EntityExtractor(known_entities=known_entities)
        resolver = EntityResolver(runtime=merged)
        extracted = extractor.extract(chunk_text)
        entity_injection_set = resolver.resolve(extracted)

        # 1c. Character Memory v2 — per-chunk selection
        character_memories = None
        if character_memory_store is not None:
            from core.character_memory_v2 import FactType
            from core.character_memory_v2.selection import select_prompt_eligible_memories
            selection_result = select_prompt_eligible_memories(
                character_memory_store,
                character_ids=None,  # All characters
                token_budget=256,
                language_profile="ko",
                include_pending=False,
                scope=character_memory_scope,
                now=metadata.get("selection_time"),
            )
            character_memories = selection_result.items

        # 1d. Context/Scene Memory — per-chunk selection
        context_selection_from_memory = None
        if enable_cross_chunk_context and context_memory_store is not None:
            from core.context_scene_memory.context_selection import select_context_for_translation
            context_selection_from_memory = select_context_for_translation(
                context_memory_store,
                chapter_id=context_memory_scope.get("chapter_id"),
                scene_id=context_memory_scope.get("scene_id"),
                sequence_index=context_memory_scope.get("sequence_index", 0),
                character_ids=context_memory_scope.get("active_character_ids"),
                source_language=context_memory_scope.get("source_language", "ko"),
                token_budget=context_memory_scope.get("token_budget", 512),
                character_context_view=(),
                character_token_budget=0,
                include_previous_translation=True,
                include_unresolved=True,
                include_experimental_inference=False,
                now=metadata.get("selection_time"),
            )
            # Override the passed context_selection if we have one from memory
            if context_selection is None:
                context_selection = context_selection_from_memory

        # 2. Prompt Builder → PromptAssembly (EXTENDED when enabled)
        builder = PromptBuilder(
            chunk_text=chunk_text,
            entity_injection_set=entity_injection_set,
            context_selection=context_selection,
            scene_state=scene_state,
            narrative_state=narrative_state,
            enable_cross_chunk_context=enable_cross_chunk_context,
            character_memories=character_memories,
        )
        assembly = builder.build(merged)

        # 3. Translation Runtime Adapter → TranslationRequest
        request = self._adapter.prepare(
            assembly,
            snapshot_id=snapshot_id,
            metadata=metadata,
        )

        # 4. Runtime Session
        if not session_id:
            session = self._session_mgr.create_session(
                snapshot_id=snapshot_id,
                prompt_hash=request.prompt_hash,
                metadata=metadata,
            )
            session_id = session.session_id
        else:
            state = self._session_mgr.get_state(session_id)
            if state is not None and state.status == RunStatus.CREATED:
                self._session_mgr.update_runtime(
                    session_id,
                    status=RunStatus.RUNNING,
                    current_chunk=current_chunk,
                    total_chunks=total_chunks,
                )
            else:
                self._session_mgr.update_runtime(
                    session_id,
                    current_chunk=current_chunk,
                    total_chunks=total_chunks,
                )

        if self._trace is None or self._trace.session_id != session_id:
            self._trace = RuntimeTraceCollector(session_id=session_id)

        self._trace = self._trace.record_chunk_start(chunk_index=current_chunk)

        # 5. Checkpoint
        from core.runtime_checkpoint.models import ProgressState, ProgressStatus
        checkpoint = self._checkpoint_mgr.create_checkpoint(
            session_id=session_id,
            chunk_index=current_chunk,
            progress=ProgressState(
                current_chunk=current_chunk,
                completed_chunks=current_chunk,
                total_chunks=total_chunks,
                status=ProgressStatus.ACTIVE,
            ),
            metadata=metadata,
        )

        self._trace = self._trace.record_checkpoint(
            checkpoint_id=checkpoint.checkpoint_id,
            chunk_index=current_chunk,
            action="CREATED",
            snapshot_id=snapshot_id,
        )

        # 6. Translation Engine → Response
        engine = engine_kwargs.pop("_engine", None) or self._engine
        if engine is None:
            response = {"status": "no_engine", "message": "TranslationEngine not configured"}
        else:
            from core.translation_runtime.models import TranslationRequest
            tr_request = TranslationRequest(
                prompt=request.prompt,
                metadata=request.metadata,
                runtime_snapshot=request.runtime_snapshot,
                snapshot_id=snapshot_id,
                prompt_hash=request.prompt_hash,
                section_count=request.section_count,
                token_count=request.token_count,
            )
            response = engine.translate_package_from_request(
                tr_request,
                source_text=chunk_text,
                chunk_index=current_chunk,
                file_name=engine_kwargs.get("file_name", "chunk.txt"),
            )

        # 7. Trace → Record completion
        duration = engine_kwargs.get("duration_ms", 0)
        self._trace = self._trace.record_chunk_finish(
            chunk_index=current_chunk,
            duration_ms=duration,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        return RuntimeExecutionResult(
            session={
                "session_id": session_id,
                "prompt_hash": request.prompt_hash,
                "snapshot_id": snapshot_id,
            },
            request={
                "prompt": request.prompt,
                "prompt_hash": request.prompt_hash,
                "section_count": request.section_count,
                "token_count": request.token_count,
            },
            response=response,
            trace={
                "session_id": session_id,
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "chunk_index": e.chunk_index,
                        "timestamp": e.timestamp,
                    }
                    for e in self._trace._events
                ],
            },
            checkpoint={
                "checkpoint_id": checkpoint.checkpoint_id,
                "session_id": session_id,
                "snapshot_id": checkpoint.snapshot_id,
                "chunk_index": current_chunk,
                "state_hash": checkpoint.state_hash,
            },
            metadata=dict(metadata),
        )

    def complete(
        self,
        session_id: str,
        success: bool = True,
    ) -> TranslationSession:
        self._session_mgr.update_runtime(
            session_id,
            status=RunStatus.COMPLETED if success else RunStatus.FAILED,
        )
        session = self._session_mgr.load_session(session_id)
        if self._trace is not None:
            event = EventType.SESSION_COMPLETED if success else EventType.SESSION_FAILED
            self._trace = self._trace.record_event(event)
        return session

    def recover(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        checkpoint = self._checkpoint_mgr.latest_checkpoint(session_id)
        if checkpoint is None:
            return None
        if self._trace is not None and self._trace.session_id == session_id:
            self._trace = self._trace.record_checkpoint(
                checkpoint_id=checkpoint.checkpoint_id,
                chunk_index=checkpoint.chunk_index,
                action="RESTORED",
                snapshot_id=checkpoint.snapshot_id,
            )
        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "session_id": checkpoint.session_id,
            "snapshot_id": checkpoint.snapshot_id,
            "chunk_index": checkpoint.chunk_index,
            "progress": {
                "current_chunk": checkpoint.progress.current_chunk,
                "completed_chunks": checkpoint.progress.completed_chunks,
                "total_chunks": checkpoint.progress.total_chunks,
                "status": checkpoint.progress.status.value,
            },
        }

    def resume(
        self,
        session_id: str,
        chunk_text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        engine_kwargs: Optional[Dict[str, Any]] = None,
    ) -> RuntimeExecutionResult:
        checkpoint = self._checkpoint_mgr.latest_checkpoint(session_id)
        if checkpoint is None:
            raise ValueError(f"No checkpoint found for session: {session_id}")

        self._checkpoint_mgr.validate_checkpoint(session_id, checkpoint.checkpoint_id)

        state = self._session_mgr.get_state(session_id)
        if state is not None and state.status != RunStatus.RUNNING:
            self._session_mgr.update_runtime(
                session_id,
                status=RunStatus.RUNNING,
                current_chunk=checkpoint.chunk_index,
            )
        else:
            self._session_mgr.update_runtime(
                session_id,
                current_chunk=checkpoint.chunk_index,
            )

        if self._trace is not None and self._trace.session_id == session_id:
            self._trace = self._trace.record_checkpoint(
                checkpoint_id=checkpoint.checkpoint_id,
                chunk_index=checkpoint.chunk_index,
                action="RESTORED",
                snapshot_id=checkpoint.snapshot_id,
            )

        return self.execute(
            chunk_text=chunk_text,
            session_id=session_id,
            snapshot_id=checkpoint.snapshot_id,
            current_chunk=checkpoint.chunk_index,
            total_chunks=checkpoint.progress.total_chunks,
            metadata=dict(metadata or {}),
            engine_kwargs=engine_kwargs,
        )

    @property
    def trace(self) -> Optional[RuntimeTraceCollector]:
        return self._trace

    @property
    def session_manager(self) -> RuntimeSessionManager:
        return self._session_mgr

    @property
    def checkpoint_manager(self) -> RuntimeCheckpointManager:
        return self._checkpoint_mgr

    @property
    def engine(self) -> Optional[Any]:
        return self._engine

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "runtime_orchestrator",
            "version": self.version,
            "knowledge": self.knowledge.manifest(),
            "session": self._session_mgr.manifest(),
            "checkpoint": {
                "version": self._checkpoint_mgr.version,
                "active_sessions": self._checkpoint_mgr.active_sessions,
                "total_checkpoints": self._checkpoint_mgr.total_checkpoints,
            },
            "adapter_version": self._adapter.version,
            "engine_configured": self._engine is not None,
            "enabled": True,
        }


__all__ = ["RuntimeOrchestrator"]