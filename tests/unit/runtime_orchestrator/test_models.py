"""Tests for Runtime Orchestrator models (RM-6.4.0)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_orchestrator.models import (
    RuntimeExecutionContext,
    RuntimeExecutionResult,
)


class TestRuntimeExecutionContext:
    def test_default_values(self):
        ctx = RuntimeExecutionContext()
        assert ctx.session_id == ""
        assert ctx.snapshot_id == ""
        assert ctx.prompt_hash == ""
        assert ctx.request_hash == ""
        assert ctx.current_chunk == 0
        assert ctx.total_chunks == 0
        assert ctx.metadata == {}
        assert ctx.version == "rm-6.4.0"

    def test_full_construction(self):
        ctx = RuntimeExecutionContext(
            session_id="sid-1",
            snapshot_id="snap-1",
            prompt_hash="ph-1",
            request_hash="rh-1",
            current_chunk=3,
            total_chunks=10,
            metadata={"book": "Dawn"},
        )
        assert ctx.session_id == "sid-1"
        assert ctx.snapshot_id == "snap-1"
        assert ctx.prompt_hash == "ph-1"
        assert ctx.request_hash == "rh-1"
        assert ctx.current_chunk == 3
        assert ctx.total_chunks == 10
        assert ctx.metadata["book"] == "Dawn"

    def test_immutable(self):
        ctx = RuntimeExecutionContext(session_id="sid-1")
        with pytest.raises(FrozenInstanceError):
            ctx.session_id = "other"

    def test_equality(self):
        c1 = RuntimeExecutionContext(session_id="a", current_chunk=1)
        c2 = RuntimeExecutionContext(session_id="a", current_chunk=1)
        c3 = RuntimeExecutionContext(session_id="a", current_chunk=2)
        assert c1 == c2
        assert c1 != c3

    def test_to_dict(self):
        ctx = RuntimeExecutionContext(
            session_id="sid-1",
            snapshot_id="snap-1",
            current_chunk=2,
            total_chunks=5,
        )
        d = ctx.to_dict()
        assert d["session_id"] == "sid-1"
        assert d["snapshot_id"] == "snap-1"
        assert d["current_chunk"] == 2
        assert d["total_chunks"] == 5
        assert d["version"] == "rm-6.4.0"

    def test_from_dict(self):
        payload = {
            "session_id": "sid-1",
            "snapshot_id": "snap-1",
            "current_chunk": 3,
            "total_chunks": 10,
            "metadata": {"book": "Dawn"},
        }
        ctx = RuntimeExecutionContext.from_dict(payload)
        assert ctx.session_id == "sid-1"
        assert ctx.snapshot_id == "snap-1"
        assert ctx.current_chunk == 3
        assert ctx.total_chunks == 10
        assert ctx.metadata["book"] == "Dawn"

    def test_roundtrip(self):
        original = RuntimeExecutionContext(
            session_id="sid-1",
            snapshot_id="snap-1",
            prompt_hash="ph-1",
            current_chunk=5,
            total_chunks=20,
            metadata={"novel": "Test"},
        )
        restored = RuntimeExecutionContext.from_dict(original.to_dict())
        assert restored == original

    def test_default_dict_values_converted(self):
        payload = {
            "session_id": "x",
            "current_chunk": "5",
            "total_chunks": "10",
        }
        ctx = RuntimeExecutionContext.from_dict(payload)
        assert ctx.current_chunk == 5
        assert ctx.total_chunks == 10

    def test_metadata_defaults_to_empty(self):
        payload = {"session_id": "s1"}
        ctx = RuntimeExecutionContext.from_dict(payload)
        assert ctx.metadata == {}


class TestRuntimeExecutionResult:
    def test_default_values(self):
        result = RuntimeExecutionResult()
        assert result.session == {}
        assert result.request == {}
        assert result.response == {}
        assert result.trace == {}
        assert result.checkpoint == {}
        assert result.metadata == {}
        assert result.version == "rm-6.4.0"

    def test_succeeded_when_success(self):
        result = RuntimeExecutionResult(response={"status": "success"})
        assert result.succeeded is True

    def test_succeeded_when_failed(self):
        result = RuntimeExecutionResult(response={"status": "failed"})
        assert result.succeeded is False

    def test_succeeded_when_no_status(self):
        result = RuntimeExecutionResult(response={})
        assert result.succeeded is False

    def test_immutable(self):
        result = RuntimeExecutionResult()
        with pytest.raises(FrozenInstanceError):
            result.session = {"new": "value"}

    def test_equality(self):
        r1 = RuntimeExecutionResult(
            session={"session_id": "s1"},
            request={"prompt_hash": "h1"},
        )
        r2 = RuntimeExecutionResult(
            session={"session_id": "s1"},
            request={"prompt_hash": "h1"},
        )
        r3 = RuntimeExecutionResult(
            session={"session_id": "s2"},
        )
        assert r1 == r2
        assert r1 != r3

    def test_full_construction(self):
        result = RuntimeExecutionResult(
            session={"session_id": "sid-1", "prompt_hash": "ph-1"},
            request={"prompt": "Hello", "prompt_hash": "ph-1"},
            response={"status": "success", "translated_at": "2024-01-01T00:00:00"},
            trace={"session_id": "sid-1", "events": []},
            checkpoint={"checkpoint_id": "cp-1", "state_hash": "abc123"},
            metadata={"novel": "Dawn"},
        )
        assert result.session["session_id"] == "sid-1"
        assert result.request["prompt"] == "Hello"
        assert result.response["status"] == "success"
        assert result.trace["session_id"] == "sid-1"
        assert result.checkpoint["checkpoint_id"] == "cp-1"
        assert result.metadata["novel"] == "Dawn"

    def test_to_dict(self):
        result = RuntimeExecutionResult(
            session={"session_id": "sid-1"},
            response={"status": "success"},
        )
        d = result.to_dict()
        assert d["session"]["session_id"] == "sid-1"
        assert d["response"]["status"] == "success"
        assert d["version"] == "rm-6.4.0"
        assert d["succeeded"] is True

    def test_from_dict(self):
        payload = {
            "session": {"session_id": "sid-1", "prompt_hash": "ph-1"},
            "request": {"prompt_hash": "ph-1"},
            "response": {"status": "success"},
            "trace": {"events": []},
            "checkpoint": {"checkpoint_id": "cp-1"},
            "metadata": {"key": "val"},
        }
        result = RuntimeExecutionResult.from_dict(payload)
        assert result.session["session_id"] == "sid-1"
        assert result.response["status"] == "success"
        assert result.checkpoint["checkpoint_id"] == "cp-1"
        assert result.metadata["key"] == "val"

    def test_roundtrip(self):
        original = RuntimeExecutionResult(
            session={"session_id": "sid-1"},
            request={"prompt_hash": "ph-1"},
            response={"status": "success"},
            trace={"events": [{"type": "CHUNK_STARTED"}]},
            checkpoint={"checkpoint_id": "cp-1", "state_hash": "abc"},
            metadata={"novel": "Dawn"},
        )
        restored = RuntimeExecutionResult.from_dict(original.to_dict())
        assert restored.session == original.session
        assert restored.request == original.request
        assert restored.response == original.response
        assert restored.trace == original.trace
        assert restored.checkpoint == original.checkpoint
        assert restored.metadata == original.metadata
        assert restored.succeeded == original.succeeded

    def test_default_dict_values(self):
        result = RuntimeExecutionResult.from_dict({})
        assert result.session == {}
        assert result.request == {}
        assert result.response == {}
        assert result.trace == {}
        assert result.checkpoint == {}
        assert result.metadata == {}