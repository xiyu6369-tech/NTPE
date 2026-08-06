"""Tests for Runtime Orchestrator manager (RM-6.4.0).

All tests use mocks. No provider calls. No network requests.
Validates orchestration, sequencing, and assembly — not translation logic.
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from core.runtime_orchestrator.models import (
    RuntimeExecutionContext,
    RuntimeExecutionResult,
)
from core.runtime_orchestrator.manager import RuntimeOrchestrator
from core.runtime_session.models import RunStatus, TranslationSession
from core.knowledge_runtime.merger import MergedRuntime
from core.prompt_runtime.builder import PromptAssembly
from core.prompt_runtime.models import PromptSection
from core.translation_runtime.models import TranslationRequest


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.translate_package_from_request.return_value = {
        "status": "success",
        "package_id": "test-pkg",
        "translated_at": "2024-01-01T00:00:00",
        "output_path": "/tmp/out.txt",
        "cache_path": "/tmp/cache.json",
        "qa": {},
        "prompt_hash": "test-hash",
    }
    return engine


class TestBuildContext:
    def test_default_context(self):
        orch = RuntimeOrchestrator()
        ctx = orch.build_context()
        assert isinstance(ctx, RuntimeExecutionContext)
        assert ctx.session_id == ""
        assert ctx.current_chunk == 0

    def test_full_context(self):
        orch = RuntimeOrchestrator()
        ctx = orch.build_context(
            session_id="sid-1",
            snapshot_id="snap-1",
            prompt_hash="ph-1",
            request_hash="rh-1",
            current_chunk=5,
            total_chunks=20,
            metadata={"book": "Dawn"},
        )
        assert ctx.session_id == "sid-1"
        assert ctx.snapshot_id == "snap-1"
        assert ctx.prompt_hash == "ph-1"
        assert ctx.request_hash == "rh-1"
        assert ctx.current_chunk == 5
        assert ctx.total_chunks == 20
        assert ctx.metadata["book"] == "Dawn"

    def test_context_immutability(self):
        orch = RuntimeOrchestrator()
        ctx1 = orch.build_context(session_id="sid-1")
        ctx2 = orch.build_context(session_id="sid-2")
        assert ctx1 != ctx2


class TestStartSession:
    def test_start_creates_session(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session(snapshot_id="snap-1")
        assert isinstance(session, TranslationSession)
        assert session.snapshot_id == "snap-1"
        assert orch.session_manager.active_sessions == 1

    def test_start_initializes_trace(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session()
        assert orch.trace is not None
        assert orch.trace.session_id == session.session_id

    def test_start_with_metadata(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session(metadata={"novel": "Dawn"})
        assert session.metadata["novel"] == "Dawn"

    def test_start_multiple_sessions(self):
        orch = RuntimeOrchestrator()
        s1 = orch.start_session()
        s2 = orch.start_session()
        assert s1.session_id != s2.session_id
        assert orch.session_manager.active_sessions == 2


class TestPrepareRequest:
    def test_prepare_returns_request_dict(self):
        orch = RuntimeOrchestrator()
        result = orch.prepare_request(
            chunk_text="Hello world",
            session_id="sid-1",
            snapshot_id="snap-1",
        )
        assert "prompt" in result
        assert "prompt_hash" in result
        assert "snapshot_id" in result
        assert "section_count" in result
        assert "token_count" in result

    def test_prepare_has_deterministic_prompt_hash(self):
        orch = RuntimeOrchestrator()
        r1 = orch.prepare_request(
            chunk_text="Same text",
            session_id="sid-1",
            snapshot_id="snap-1",
        )
        r2 = orch.prepare_request(
            chunk_text="Same text",
            session_id="sid-1",
            snapshot_id="snap-1",
        )
        assert r1["prompt_hash"] == r2["prompt_hash"]

    def test_prepare_different_text_different_hash(self):
        orch = RuntimeOrchestrator()
        r1 = orch.prepare_request(
            chunk_text="Text A",
            session_id="sid-1",
            snapshot_id="snap-1",
        )
        r2 = orch.prepare_request(
            chunk_text="Text B",
            session_id="sid-1",
            snapshot_id="snap-1",
        )
        assert r1["prompt_hash"] != r2["prompt_hash"]

    def test_prepare_saves_session(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        result = orch.prepare_request(
            chunk_text="Hello",
            session_id=sess.session_id,
            snapshot_id="snap-1",
        )
        session = orch.session_manager.load_session(sess.session_id)
        assert session is not None


class TestExecute:
    def test_execute_without_engine(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        result = orch.execute(
            chunk_text="Test chunk",
            current_chunk=0,
            total_chunks=10,
        )
        assert isinstance(result, RuntimeExecutionResult)
        assert result.response["status"] == "no_engine"

    def test_execute_with_mock_engine(self, mock_engine):
        orch = RuntimeOrchestrator()
        orch.set_engine(mock_engine)
        orch.start_session(snapshot_id="snap-1")
        result = orch.execute(
            chunk_text="Test chunk",
            current_chunk=0,
            total_chunks=10,
        )
        assert result.response["status"] == "success"
        assert len(result.request["prompt"]) > 0
        assert result.session["session_id"]
        assert result.checkpoint["checkpoint_id"]
        mock_engine.translate_package_from_request.assert_called_once()

    def test_execute_creates_checkpoint(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        result = orch.execute(
            chunk_text="Test chunk",
            current_chunk=0,
            total_chunks=10,
        )
        assert result.checkpoint["checkpoint_id"]
        assert orch.checkpoint_manager.total_checkpoints == 1

    def test_execute_records_trace_events(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        orch.execute(
            chunk_text="Test chunk",
            current_chunk=0,
            total_chunks=10,
        )
        assert orch.trace is not None
        assert len(orch.trace.chunks) >= 1

    def test_execute_preserves_prompt_in_result(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        result = orch.execute(
            chunk_text="Test content",
            current_chunk=0,
            total_chunks=10,
        )
        assert "prompt" in result.request
        assert len(result.request["prompt"]) > 0

    def test_execute_with_explicit_session_id(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id
        orch.session_manager.update_runtime(
            sid, status=RunStatus.RUNNING
        )
        result = orch.execute(
            chunk_text="Test chunk",
            session_id=sid,
            current_chunk=0,
            total_chunks=10,
        )
        assert result.session["session_id"] == sid

    def test_execute_deterministic_same_input(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id
        r1 = orch.execute(
            chunk_text="Deterministic test",
            session_id=sid,
            current_chunk=0,
            total_chunks=5,
        )
        r2 = orch.execute(
            chunk_text="Deterministic test",
            session_id=sid,
            current_chunk=0,
            total_chunks=5,
        )
        assert r1.request["prompt_hash"] == r2.request["prompt_hash"]


class TestComplete:
    def test_complete_success(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session()
        orch.session_manager.update_runtime(
            session.session_id, status=RunStatus.RUNNING
        )
        orch.complete(session.session_id, success=True)
        state = orch.session_manager.get_state(session.session_id)
        assert state.status == RunStatus.COMPLETED

    def test_complete_failure(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session()
        orch.session_manager.update_runtime(
            session.session_id, status=RunStatus.RUNNING
        )
        orch.complete(session.session_id, success=False)
        state = orch.session_manager.get_state(session.session_id)
        assert state.status == RunStatus.FAILED


class TestRecover:
    def test_recover_no_checkpoints(self):
        orch = RuntimeOrchestrator()
        session = orch.start_session()
        result = orch.recover(session.session_id)
        assert result is None

    def test_recover_with_checkpoint(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session()
        orch.execute(
            chunk_text="Test chunk",
            session_id=sess.session_id,
            current_chunk=3,
            total_chunks=10,
        )
        result = orch.recover(sess.session_id)
        assert result is not None
        assert result["chunk_index"] == 3

    def test_recover_returns_latest(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id
        orch.execute(
            chunk_text="Chunk 0",
            session_id=sid,
            current_chunk=0,
            total_chunks=5,
        )
        orch.execute(
            chunk_text="Chunk 1",
            session_id=sid,
            current_chunk=1,
            total_chunks=5,
        )
        orch.execute(
            chunk_text="Chunk 2",
            session_id=sid,
            current_chunk=2,
            total_chunks=5,
        )
        result = orch.recover(sid)
        assert result["chunk_index"] == 2


class TestResume:
    def test_resume_from_checkpoint(self, mock_engine):
        orch = RuntimeOrchestrator()
        orch.set_engine(mock_engine)
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id

        orch.execute(
            chunk_text="Chunk 0",
            session_id=sid,
            current_chunk=0,
            total_chunks=5,
        )

        orch.execute(
            chunk_text="Chunk 1",
            session_id=sid,
            current_chunk=1,
            total_chunks=5,
        )

        result = orch.resume(
            session_id=sid,
            chunk_text="Chunk 2",
        )
        assert result.response["status"] == "success"
        mock_engine.translate_package_from_request.assert_called()

    def test_resume_no_checkpoint_raises(self):
        orch = RuntimeOrchestrator()
        orch.start_session()
        with pytest.raises(ValueError):
            orch.resume(session_id="no-such-session", chunk_text="text")


class TestCheckpointHook:
    def test_checkpoint_created_during_execute(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        result = orch.execute(
            chunk_text="Test",
            current_chunk=0,
            total_chunks=10,
        )
        assert orch.checkpoint_manager.total_checkpoints == 1
        assert result.checkpoint["checkpoint_id"]

    def test_multiple_checkpoints_per_session(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id
        orch.execute(
            chunk_text="C0",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        orch.execute(
            chunk_text="C1",
            session_id=sid,
            current_chunk=1,
            total_chunks=3,
        )
        orch.execute(
            chunk_text="C2",
            session_id=sid,
            current_chunk=2,
            total_chunks=3,
        )
        assert orch.checkpoint_manager.total_checkpoints == 3


class TestTraceHook:
    def test_trace_events_recorded(self):
        orch = RuntimeOrchestrator()
        orch.start_session(snapshot_id="snap-1")
        orch.execute(
            chunk_text="Test",
            current_chunk=0,
            total_chunks=5,
        )
        assert orch.trace is not None
        assert len(orch.trace.chunks) >= 1

    def test_trace_chunk_finish(self):
        orch = RuntimeOrchestrator()
        orch.start_session()
        orch.execute(
            chunk_text="Test",
            current_chunk=2,
            total_chunks=10,
        )
        chunks = orch.trace.chunks
        assert len(chunks) >= 1
        assert chunks[-1].chunk_index == 2
        assert chunks[-1].session_id

    def test_trace_preserves_ordering(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id
        orch.execute(
            chunk_text="C0",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        orch.execute(
            chunk_text="C1",
            session_id=sid,
            current_chunk=1,
            total_chunks=3,
        )
        seen = set()
        indices = [
            c.chunk_index for c in orch.trace.chunks
            if c.chunk_index not in seen and not seen.add(c.chunk_index)
        ]
        assert indices[:2] == [0, 1]


class TestRecoveryFlow:
    def test_recover_checkpoint_hook(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        orch.execute(
            chunk_text="Test",
            session_id=sess.session_id,
            current_chunk=5,
            total_chunks=20,
        )
        result = orch.recover(sess.session_id)
        assert result is not None
        assert result["chunk_index"] == 5
        assert result["progress"]["current_chunk"] == 5
        assert result["progress"]["total_chunks"] == 20

    def test_recovery_resume_uses_last_checkpoint(self, mock_engine):
        orch = RuntimeOrchestrator()
        orch.set_engine(mock_engine)
        sess = orch.start_session(snapshot_id="snap-1")
        sid = sess.session_id

        orch.execute(
            chunk_text="C0",
            session_id=sid,
            current_chunk=0,
            total_chunks=10,
        )
        orch.execute(
            chunk_text="C1",
            session_id=sid,
            current_chunk=1,
            total_chunks=10,
        )

        result = orch.resume(
            session_id=sid,
            chunk_text="C2",
        )
        assert result.session["session_id"] == sid


class TestDeterministicExecution:
    def test_same_input_same_prompt_hash(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-det")
        sid = sess.session_id

        r1 = orch.execute(
            chunk_text="Same exact text for determinism",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        r2 = orch.execute(
            chunk_text="Same exact text for determinism",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        assert r1.request["prompt_hash"] == r2.request["prompt_hash"]

    def test_different_input_different_hash(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-det")
        sid = sess.session_id

        r1 = orch.execute(
            chunk_text="Text variant A",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        r2 = orch.execute(
            chunk_text="Text variant B different",
            session_id=sid,
            current_chunk=0,
            total_chunks=3,
        )
        assert r1.request["prompt_hash"] != r2.request["prompt_hash"]


class TestNoProviderNetworkCalls:
    def test_execute_without_engine_no_network(self):
        orch = RuntimeOrchestrator()
        orch.start_session()
        result = orch.execute(
            chunk_text="Hello",
            current_chunk=0,
            total_chunks=1,
        )
        assert result.response["status"] == "no_engine"

    def test_mock_engine_never_calls_provider(self, mock_engine):
        orch = RuntimeOrchestrator()
        orch.set_engine(mock_engine)
        sess = orch.start_session()
        orch.execute(
            chunk_text="Hello",
            session_id=sess.session_id,
            current_chunk=0,
            total_chunks=1,
        )
        assert mock_engine.translate_package_from_request.called

    def test_prepare_request_no_network(self):
        orch = RuntimeOrchestrator()
        r = orch.prepare_request(chunk_text="Hello")
        assert "prompt" in r

    def test_recover_no_network(self):
        orch = RuntimeOrchestrator()
        sess = orch.start_session(snapshot_id="snap-1")
        orch.execute(
            chunk_text="Test",
            session_id=sess.session_id,
            current_chunk=0,
            total_chunks=3,
        )
        result = orch.recover(sess.session_id)
        assert result is not None
        assert "checkpoint_id" in result


class TestOrchestratorIntegration:
    def test_full_flow_without_engine(self):
        orch = RuntimeOrchestrator()

        session = orch.start_session(snapshot_id="snap-full")
        assert session.session_id
        assert orch.session_manager.active_sessions == 1

        result = orch.execute(
            chunk_text="Full flow test",
            session_id=session.session_id,
            current_chunk=0,
            total_chunks=3,
        )
        assert isinstance(result, RuntimeExecutionResult)
        assert result.session["session_id"]

        orch.complete(session.session_id, success=True)
        state = orch.session_manager.get_state(session.session_id)
        assert state.status == RunStatus.COMPLETED

    def test_manifest_returns_expected_keys(self):
        orch = RuntimeOrchestrator()
        manifest = orch.manifest()
        assert manifest["name"] == "runtime_orchestrator"
        assert manifest["version"] == "rm-6.4.0"
        assert manifest["enabled"] is True
        assert "knowledge" in manifest
        assert "session" in manifest
        assert "checkpoint" in manifest
        assert "engine_configured" in manifest