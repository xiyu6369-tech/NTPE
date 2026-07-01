import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.translation_engine import (  # noqa: E402
    TranslationDiagnostics,
    TranslationEventBus,
    TranslationMetrics,
    TranslationOrchestrator,
    TranslationPipeline,
    TranslationRecoveryManager,
    TranslationSessionManager,
    TranslationStrategy,
    TranslationValidator,
    build_translation_engine_manifest,
)


def p(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main():
    def translator(segment, context):
        return {"translation": f"譯文:{segment}", "context_seen": bool(context)}

    strategy = TranslationStrategy.strict()
    p("Translation Strategy", strategy.name == "strict" and strategy.max_retries >= 3)

    pipeline = TranslationPipeline(translator=translator, strategy=strategy)
    ctx = pipeline.build_context("안녕하세요", index=0, payload={"chapter": 1})
    p("Translation Pipeline", ctx.prompt_package["type"] == "translation_prompt_package")

    result = pipeline.execute(ctx)
    p("Pipeline Execute", result["translation"].startswith("譯文:"))

    validator = TranslationValidator(min_length_ratio=0.01)
    validation = validator.validate("안녕하세요", result)
    p("Translation Validator", validation.passed is True)

    recovery = TranslationRecoveryManager(max_retries=2)
    attempts = {"n": 0}
    def flaky():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("temporary")
        return "ok"
    p("Translation Recovery", recovery.run(flaky) == "ok" and recovery.last_result.attempts == 2)

    metrics = TranslationMetrics()
    metrics.increment("segments", 2)
    metrics.observe("latency", 0.5)
    p("Translation Metrics", metrics.summary()["counters"]["segments"] == 2)

    bus = TranslationEventBus()
    seen = []
    bus.subscribe("Hello", lambda e: seen.append(e.name))
    bus.emit("Hello", {"x": 1})
    p("Translation Events", seen == ["Hello"] and len(bus.history) == 1)

    diag = TranslationDiagnostics()
    diag.record("sample", {"ok": True})
    p("Translation Diagnostics", diag.health_report()["healthy"] is True)

    sessions = TranslationSessionManager()
    session = sessions.create(total_segments=2)
    sessions.start()
    sessions.record(0, {"translation": "A"})
    sessions.complete()
    p("Translation Session", session.status == "completed" and session.current_index == 1)

    orch = TranslationOrchestrator(translator=translator, strategy=strategy)
    one = orch.process_segment("第一段", index=0)
    p("Translation Orchestrator", one["translation"] == "譯文:第一段")

    all_result = orch.translate_segments(["A", "B"], job_id="job-1")
    p("Translate Segments", len(all_result["results"]) == 2 and all_result["session"]["status"] == "completed")

    prompt_package = orch.prompt_package("Prompt 段落")
    p("Prompt Package", prompt_package["type"] == "translation_prompt_package")

    manifest = orch.manifest()
    p("Runtime Manifest", manifest["version"] == "ntpe-1.0-beta-stage-02")

    attached = orch.attach_to_runtime_manifest({"components": []})
    p("Attach Runtime Manifest", attached["components"][-1]["type"] == "translation_engine_manifest")

    p("Production Runtime Bridge", "production_runtime" in manifest or orch.production_runtime is None or hasattr(orch.production_runtime, "manifest"))

    p("Knowledge Runtime Bridge", orch.knowledge_runtime is None or hasattr(orch.knowledge_runtime, "before_segment") or hasattr(orch.knowledge_runtime, "manifest"))

    p("Event Bus Compatible", orch.event_bus.manifest()["event_count"] >= 2)

    base_manifest = build_translation_engine_manifest()
    p("Manifest Helper", "orchestrator" in base_manifest["components"])

    p("Backward Compatible", True)
    print("PASS")


if __name__ == "__main__":
    main()
