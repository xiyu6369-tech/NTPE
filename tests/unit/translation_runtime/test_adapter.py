"""Tests for Translation Runtime Adapter (RM-6.2.2)."""

import pytest

from core.knowledge_runtime.merger import MergedKnowledge, MergedRuntime
from core.prompt_runtime.builder import PromptBuilder, build_prompt
from core.translation_runtime.adapter import (
    TranslationRuntimeAdapter,
    _assemble_prompt,
    _compute_prompt_hash,
    _count_tokens_approximate,
)
from core.translation_runtime.models import TranslationRequest, TranslationResponse


def make_runtime(domains: dict) -> MergedRuntime:
    merged_domains = {}
    for name, entries in domains.items():
        merged_domains[name] = MergedKnowledge(
            domain=name,
            entries=entries,
            strategy="key_override",
        )
    return MergedRuntime(domains=merged_domains)


class TestAssemblePrompt:
    def test_flattens_sections(self):
        from core.prompt_runtime.models import SystemSection, ChunkSection
        sections = [
            SystemSection(content="You are a translator."),
            ChunkSection(content="Hello world."),
        ]
        result = _assemble_prompt(sections)
        assert "[System]" in result
        assert "[Chunk]" in result
        assert "You are a translator." in result
        assert "Hello world." in result

    def test_empty_section_preserved(self):
        from core.prompt_runtime.models import SystemSection
        sections = [SystemSection(content="")]
        result = _assemble_prompt(sections)
        assert "[System]" in result

    def test_no_sections(self):
        result = _assemble_prompt([])
        assert result == ""


class TestCountTokens:
    def test_empty_text(self):
        assert _count_tokens_approximate("") == 0

    def test_short_text(self):
        assert _count_tokens_approximate("hello") == 1

    def test_typical_text(self):
        tokens = _count_tokens_approximate("a" * 100)
        assert tokens == 25

    def test_cjk_text(self):
        tokens = _count_tokens_approximate("這是一段中文字")
        assert _count_tokens_approximate("這是一段中文字") >= 1


class TestComputePromptHash:
    def test_deterministic(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        a1 = build_prompt(runtime, "text")
        a2 = build_prompt(runtime, "text")
        h1 = _compute_prompt_hash(a1, "snap-1", {})
        h2 = _compute_prompt_hash(a2, "snap-1", {})
        assert h1 == h2

    def test_different_snapshot_different_hash(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        a = build_prompt(runtime, "text")
        h1 = _compute_prompt_hash(a, "snap-1", {})
        h2 = _compute_prompt_hash(a, "snap-2", {})
        assert h1 != h2

    def test_different_runtime_different_hash(self):
        r1 = make_runtime({"character": {"Hero": "knight"}})
        r2 = make_runtime({"character": {"Hero": "mage"}})
        a1 = build_prompt(r1, "text")
        a2 = build_prompt(r2, "text")
        assert _compute_prompt_hash(a1, "snap", {}) != _compute_prompt_hash(a2, "snap", {})

    def test_same_inputs_same_hash(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        a = build_prompt(runtime, "text")
        h1 = _compute_prompt_hash(a, "snap", {"key": "val"})
        h2 = _compute_prompt_hash(a, "snap", {"key": "val"})
        assert h1 == h2


class TestTranslationRuntimeAdapter:
    def test_prepare_returns_translation_request(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        assembly = build_prompt(runtime, "Translate me.")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly, snapshot_id="snap-001")
        assert isinstance(request, TranslationRequest)

    def test_prepare_has_prompt(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        assembly = build_prompt(runtime, "Translate me.")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        assert request.prompt
        assert "[System]" in request.prompt
        assert "Translate me." in request.prompt

    def test_prepare_sets_section_count(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        assert request.section_count == 7

    def test_prepare_sets_token_count(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        assert request.token_count > 0

    def test_prepare_sets_build_timestamp(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        assert request.build_timestamp

    def test_prepare_sets_snapshot_id(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly, snapshot_id="snap-abc")
        assert request.snapshot_id == "snap-abc"

    def test_prepare_propagates_metadata(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(
            assembly,
            metadata={"novel": "Dawn"},
        )
        assert request.metadata["novel"] == "Dawn"

    def test_prepare_sets_prompt_hash(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly, snapshot_id="snap-1")
        assert len(request.prompt_hash) == 64

    def test_prepare_runtime_snapshot(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        snap = request.runtime_snapshot
        assert snap["prompt_section_count"] == 7
        assert snap["prompt_text_length"] > 0
        assert snap["token_count"] > 0
        assert snap["adapter_version"] == adapter.version
        assert snap["prompt_hash"] == request.prompt_hash

    def test_deterministic_request(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        a1 = build_prompt(runtime, "text")
        a2 = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        r1 = adapter.prepare(a1, snapshot_id="snap-1")
        r2 = adapter.prepare(a2, snapshot_id="snap-1")
        assert r1.prompt_hash == r2.prompt_hash
        assert r1.prompt == r2.prompt
        assert r1.section_count == r2.section_count
        assert r1.token_count == r2.token_count
        assert r1.snapshot_id == r2.snapshot_id

    def test_different_runtime_different_request(self):
        r1 = make_runtime({"character": {"Hero": "knight"}})
        r2 = make_runtime({"character": {"Hero": "mage"}})
        a1 = build_prompt(r1, "text")
        a2 = build_prompt(r2, "text")
        adapter = TranslationRuntimeAdapter()
        req1 = adapter.prepare(a1, snapshot_id="snap-1")
        req2 = adapter.prepare(a2, snapshot_id="snap-1")
        assert req1.prompt_hash != req2.prompt_hash

    def test_empty_runtime_prepare(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        assert request.prompt
        assert request.section_count == 7
        assert "[System]" in request.prompt
        assert "[Chunk]" in request.prompt

    def test_identical_runtime_same_hash(self):
        runtime = make_runtime({"character": {"Hero": "knight"}})
        a1 = build_prompt(runtime, "text")
        a2 = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        r1 = adapter.prepare(a1, snapshot_id="snap")
        r2 = adapter.prepare(a2, snapshot_id="snap")
        assert r1.prompt_hash == r2.prompt_hash

    def test_prepare_response(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        response = adapter.prepare_response(request)
        assert isinstance(response, TranslationResponse)
        assert response.prompt == request.prompt
        assert response.request == request

    def test_get_request_found(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        found = adapter.get_request(request.prompt_hash)
        assert found == request

    def test_get_request_not_found(self):
        adapter = TranslationRuntimeAdapter()
        assert adapter.get_request("no-such-hash") is None

    def test_manifest(self):
        adapter = TranslationRuntimeAdapter()
        manifest = adapter.manifest()
        assert manifest["name"] == "translation_runtime_adapter"
        assert manifest["version"] == adapter.version
        assert manifest["enabled"] is True

    def test_serialization_roundtrip(self):
        runtime = make_runtime({"character": {"Hero": "knight"}, "glossary": {"術語": "term"}})
        assembly = build_prompt(runtime, "Source text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly, snapshot_id="snap-001", metadata={"novel": "Test"})
        data = request.to_dict()
        restored = TranslationRequest.from_dict(data)
        assert restored == request
        assert restored.prompt == request.prompt
        assert restored.section_count == request.section_count

    def test_metadata_generation(self):
        runtime = make_runtime({"character": {"a": "b"}})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly, snapshot_id="snap-001")
        assert request.snapshot_id == "snap-001"
        assert request.prompt_hash
        assert request.section_count == 7
        assert request.token_count > 0
        assert request.build_timestamp

    def test_no_translation_engine_calls(self):
        runtime = make_runtime({})
        assembly = build_prompt(runtime, "text")
        adapter = TranslationRuntimeAdapter()
        request = adapter.prepare(assembly)
        response = adapter.prepare_response(request)
        assert response.prompt == request.prompt
        assert response.version == "rm-6.2.2"