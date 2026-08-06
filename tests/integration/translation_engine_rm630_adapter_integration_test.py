"""RM-6.3.0 — Translation Engine Integration Tests.

Verifies that TranslationEngine.translate_package_from_request(TranslationRequest)
correctly consumes an immutable TranslationRequest from the Runtime pipeline.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_engine import provider_runtime
from core.translation_engine.translation_engine import TranslationEngine
from core.translation_runtime.adapter import TranslationRuntimeAdapter
from core.translation_runtime.models import TranslationRequest
from core.prompt_runtime.builder import PromptAssembly
from core.prompt_runtime.models import SystemSection, ChunkSection, CharacterSection


_SOURCE = "정태의가 숨을 들이켰다."
_EXPECTED = "鄭泰義倒抽一口氣。\n"
_SP = "You are a professional translator."


class FakeNvidiaClient:
    calls = []

    def __init__(self, **kwargs):
        pass

    def chat(self, *, model, system_prompt, user_prompt, temperature, top_p, max_tokens):
        self.__class__.calls.append({
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        })
        return _EXPECTED


def _make_fixture():
    """Return (engine, request, tmpdir) — caller must hold tmpdir alive."""
    tmpdir = tempfile.TemporaryDirectory()
    root = Path(tmpdir.name)
    (root / "config").mkdir(parents=True)
    (root / "config" / "provider_config.json").write_text(json.dumps({
        "default_provider": "nvidia",
        "translation_engine_v3": {
            "fallback_models": [],
            "retry_defaults": {"max_attempts": 1, "base_delay_seconds": 0.0},
        },
        "providers": {"nvidia": {"env_var": "NVIDIA_API_KEY", "default_model": "test-model"}},
    }), encoding="utf-8")

    sections = [
        SystemSection(content=_SP),
        CharacterSection(content="鄭泰義: protagonist"),
        ChunkSection(content=_SOURCE),
    ]
    assembly = PromptAssembly(
        sections=sections,
        metadata={"runtime_version": "rm-6.2.0"},
        version="rm-6.2.0",
    )
    adapter = TranslationRuntimeAdapter()
    req = adapter.prepare(assembly, snapshot_id="rm630-test", metadata={
        "package_id": "rm630-test",
        "model_profile": {"model": "test-model", "temperature": 0.15,
                          "top_p": 0.85, "max_output_tokens": 128},
        "system_prompt": _SP,
        "source": {"chunk_text": _SOURCE, "char_count": len(_SOURCE)},
    })
    return TranslationEngine(root), req, root


def _setup_patch():
    FakeNvidiaClient.calls = []
    old_cl = provider_runtime.NvidiaClient
    old_key = os.environ.get("NVIDIA_API_KEY")
    provider_runtime.NvidiaClient = FakeNvidiaClient
    os.environ["NVIDIA_API_KEY"] = "test-key"
    return old_cl, old_key


def _undo(old_cl, old_key):
    provider_runtime.NvidiaClient = old_cl
    if old_key is None:
        os.environ.pop("NVIDIA_API_KEY", None)
    else:
        os.environ["NVIDIA_API_KEY"] = old_key


# ── Golden Regression ──────────────────────────────────────────────

def test_rm630_golden() -> None:
    old_cl, old_key = _setup_patch()
    try:
        engine, req, _ = _make_fixture()
        result = engine.translate_package_from_request(
            req, source_text=_SOURCE, chunk_index=1, file_name="golden.txt")

        assert result["status"] == "success"
        assert result["package_id"] == "rm630-test"
        assert result["prompt_hash"] == req.prompt_hash
        assert result["snapshot_id"] == "rm630-test"
        assert result["request_version"] == "rm-6.2.2"
        assert "output_path" in result
        assert "cache_path" in result
        assert result["qa"]["passed"] is True
        assert result["qa"]["source_length"] == len(_SOURCE)

        call = FakeNvidiaClient.calls[0]
        assert call["model"] == "test-model"
        assert call["system_prompt"] == _SP
        assert _SOURCE in call["user_prompt"]
        assert call["temperature"] == 0.15
        assert call["top_p"] == 0.85
        assert call["max_tokens"] == 128

        out = Path(result["output_path"]).read_text(encoding="utf-8")
        assert _EXPECTED.strip() in out

        cache = json.loads(Path(result["cache_path"]).read_text(encoding="utf-8"))
        assert cache["result"]["status"] == "success"
        assert cache["request"]["prompt_hash"] == req.prompt_hash
        assert cache["request"]["section_count"] == 3
        assert _EXPECTED.strip() in cache["translation"]
    finally:
        _undo(old_cl, old_key)


# ── Prompt Hash Consistency ────────────────────────────────────────

def test_rm630_prompt_hash_deterministic() -> None:
    assembly = PromptAssembly(
        sections=[SystemSection(content="sp"), ChunkSection(content="x")],
        metadata={}, version="rm-6.2.0",
    )
    adapter = TranslationRuntimeAdapter()
    meta = {"model_profile": {"model": "m"}, "system_prompt": "sp"}
    r1 = adapter.prepare(assembly, snapshot_id="s1", metadata=meta)
    r2 = adapter.prepare(assembly, snapshot_id="s1", metadata=meta)
    assert r1.prompt_hash == r2.prompt_hash
    assert len(r1.prompt_hash) == 64

    r3 = adapter.prepare(assembly, snapshot_id="s2", metadata=meta)
    assert r3.prompt_hash != r1.prompt_hash


# ── Provider Request Parity ─────────────────────────────────────────

def test_rm630_provider_parity() -> None:
    old_cl, old_key = _setup_patch()
    try:
        engine, req, tmpdir = _make_fixture()
        _ = engine.translate_package_from_request(
            req, source_text=_SOURCE, chunk_index=0, file_name="parity.txt")

        call = FakeNvidiaClient.calls[0]
        assert call["model"] == "test-model"
        assert call["temperature"] == 0.15
        assert call["top_p"] == 0.85
        assert call["max_tokens"] == 128
        assert call["system_prompt"] == _SP
        assert _SOURCE in call["user_prompt"]
    finally:
        _undo(old_cl, old_key)


# ── Output Compatibility ───────────────────────────────────────────

def test_rm630_output_structure() -> None:
    old_cl, old_key = _setup_patch()
    try:
        engine, req, tmpdir = _make_fixture()
        result = engine.translate_package_from_request(
            req, source_text=_SOURCE, chunk_index=0, file_name="out.txt")

        required = {"status", "package_id", "translated_at", "output_path",
                    "cache_path", "qa", "provider"}
        assert required <= set(result.keys())
        assert result["prompt_hash"] == req.prompt_hash
        assert result["snapshot_id"] == "rm630-test"
        assert result["request_version"] == "rm-6.2.2"
        assert result["qa"]["korean_residue_count"] >= 0
        assert "source_length" in result["qa"]
        assert "translation_length" in result["qa"]
    finally:
        _undo(old_cl, old_key)


# ── Single Provider Call ───────────────────────────────────────────

def test_rm630_single_provider_call() -> None:
    old_cl, old_key = _setup_patch()
    try:
        engine, req, tmpdir = _make_fixture()
        assert len(FakeNvidiaClient.calls) == 0
        _ = engine.translate_package_from_request(
            req, source_text=_SOURCE, chunk_index=0, file_name="single.txt")
        assert len(FakeNvidiaClient.calls) == 1
    finally:
        _undo(old_cl, old_key)


# ── Error Handling ─────────────────────────────────────────────────

def test_rm630_error_graceful_degrade() -> None:
    old_key = os.environ.get("NVIDIA_API_KEY")
    os.environ.pop("NVIDIA_API_KEY", None)
    try:
        from core.translation_runtime.models import TranslationRequest as TR
        req = TR(
            prompt="test",
            metadata={"system_prompt": "sp",
                       "model_profile": {"model": "no-such-model",
                                         "temperature": 0.15, "top_p": 0.85,
                                         "max_output_tokens": 128}},
            runtime_snapshot={},
            snapshot_id="err-test",
            prompt_hash="ff" * 32,
        )
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        engine = TranslationEngine(root)
        result = engine.translate_package_from_request(
            req, source_text="test", chunk_index=0, file_name="err.txt")
        assert result["status"] == "failed"
        assert "error" in result
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


# ── Lifecycle Traceability ─────────────────────────────────────────

def test_rm630_lifecycle() -> None:
    old_cl, old_key = _setup_patch()
    try:
        engine, req, tmpdir = _make_fixture()
        assert req.section_count > 0
        assert req.token_count > 0
        assert req.build_timestamp
        assert req.prompt_hash
        assert _SOURCE in req.prompt

        result = engine.translate_package_from_request(
            req, source_text=_SOURCE, chunk_index=0, file_name="life.txt")
        assert result["prompt_hash"] == req.prompt_hash
        cache = json.loads(Path(result["cache_path"]).read_text(encoding="utf-8"))
        assert cache["request"]["section_count"] == 3
        assert cache["runtime_snapshot"]["prompt_section_count"] == 3
        assert cache["runtime_snapshot"]["token_count"] == req.token_count
    finally:
        _undo(old_cl, old_key)


if __name__ == "__main__":
    test_rm630_prompt_hash_deterministic()
    print("PASS: prompt_hash is deterministic")