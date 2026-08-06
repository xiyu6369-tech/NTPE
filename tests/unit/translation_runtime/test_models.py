"""Tests for Translation Runtime models (RM-6.2.2)."""

from dataclasses import FrozenInstanceError

import pytest

from core.translation_runtime.models import (
    TranslationRequest,
    TranslationResponse,
    _deterministic_hash,
    _section_content_hash,
)


class TestDeterministicHash:
    def test_same_inputs_same_hash(self):
        h1 = _deterministic_hash("a", "b", "c")
        h2 = _deterministic_hash("a", "b", "c")
        assert h1 == h2
        assert len(h1) == 64

    def test_different_inputs_different_hash(self):
        h1 = _deterministic_hash("a", "b", "c")
        h2 = _deterministic_hash("a", "b", "d")
        assert h1 != h2

    def test_empty_inputs(self):
        h = _deterministic_hash()
        assert len(h) == 64

    def test_single_input(self):
        h = _deterministic_hash("hello")
        assert len(h) == 64

    def test_part_count_matters(self):
        h1 = _deterministic_hash("a", "b", "c")
        h2 = _deterministic_hash("a", "bc")
        assert h1 != h2


class TestSectionContentHash:
    def test_same_sections_same_hash(self):
        sections = [
            {"name": "System", "content": "You are a translator."},
            {"name": "Character", "content": "Hero: knight"},
        ]
        h1 = _section_content_hash(sections)
        h2 = _section_content_hash(sections)
        assert h1 == h2

    def test_different_content_different_hash(self):
        s1 = [{"name": "System", "content": "You are a translator."}]
        s2 = [{"name": "System", "content": "You are a reviewer."}]
        assert _section_content_hash(s1) != _section_content_hash(s2)

    def test_different_name_different_hash(self):
        s1 = [{"name": "System", "content": "text"}]
        s2 = [{"name": "Character", "content": "text"}]
        assert _section_content_hash(s1) != _section_content_hash(s2)

    def test_empty_sections(self):
        h = _section_content_hash([])
        assert len(h) == 64

    def test_metadata_not_in_hash(self):
        s1 = [{"name": "System", "content": "text", "metadata": {"a": 1}}]
        s2 = [{"name": "System", "content": "text", "metadata": {"a": 2}}]
        assert _section_content_hash(s1) == _section_content_hash(s2)


class TestTranslationRequest:
    def test_immutable(self):
        req = TranslationRequest(prompt="test")
        with pytest.raises(FrozenInstanceError):
            req.prompt = "changed"

    def test_to_dict_roundtrip(self):
        req = TranslationRequest(
            prompt="Translate this.",
            metadata={"source": "novel"},
            runtime_snapshot={"token_count": 10},
            snapshot_id="snap-001",
            prompt_hash="abc123",
            section_count=7,
            token_count=100,
        )
        data = req.to_dict()
        restored = TranslationRequest.from_dict(data)
        assert restored == req
        assert restored.prompt == "Translate this."
        assert restored.metadata["source"] == "novel"
        assert restored.runtime_snapshot["token_count"] == 10
        assert restored.snapshot_id == "snap-001"
        assert restored.prompt_hash == "abc123"
        assert restored.section_count == 7
        assert restored.token_count == 100

    def test_defaults(self):
        req = TranslationRequest(prompt="test")
        assert req.metadata == {}
        assert req.runtime_snapshot == {}
        assert req.snapshot_id == ""
        assert req.prompt_hash == ""
        assert req.section_count == 0
        assert req.token_count == 0
        assert req.build_timestamp
        assert req.version == "rm-6.2.2"

    def test_id_is_snapshot_id(self):
        req = TranslationRequest(prompt="test", snapshot_id="snap-001")
        assert req.id == req.snapshot_id

    def test_equality_excluding_timestamp(self):
        r1 = TranslationRequest(prompt="test", snapshot_id="A")
        r2 = TranslationRequest(prompt="test", snapshot_id="A")
        # Timestamps differ, so compare fields except build_timestamp
        assert r1.prompt == r2.prompt
        assert r1.snapshot_id == r2.snapshot_id
        assert r1.prompt_hash == r2.prompt_hash
        assert r1.section_count == r2.section_count
        assert r1.token_count == r2.token_count

    def test_same_content_different_hash(self):
        r1 = TranslationRequest(prompt="test", prompt_hash="h1")
        r2 = TranslationRequest(prompt="test", prompt_hash="h2")
        assert r1 != r2

    def test_serialization_preserves_timestamp(self):
        req = TranslationRequest(prompt="test")
        data = req.to_dict()
        restored = TranslationRequest.from_dict(data)
        assert restored.build_timestamp == req.build_timestamp


class TestTranslationResponse:
    def test_immutable(self):
        req = TranslationRequest(prompt="test")
        resp = TranslationResponse(prompt="test", request=req)
        with pytest.raises(FrozenInstanceError):
            resp.prompt = "changed"

    def test_wraps_request(self):
        req = TranslationRequest(prompt="assemble me")
        resp = TranslationResponse(prompt=req.prompt, request=req)
        assert resp.prompt == req.prompt
        assert resp.request == req

    def test_to_dict_roundtrip(self):
        req = TranslationRequest(prompt="test", snapshot_id="S1")
        resp = TranslationResponse(prompt=req.prompt, request=req)
        data = resp.to_dict()
        restored = TranslationResponse.from_dict(data)
        assert restored.prompt == resp.prompt
        assert restored.request.prompt == req.prompt
        assert restored.request.snapshot_id == req.snapshot_id

    def test_version(self):
        resp = TranslationResponse(
            prompt="test",
            request=TranslationRequest(prompt="test"),
        )
        assert resp.version == "rm-6.2.2"