from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import time
from pathlib import Path

from core.character_memory_v2 import (
    AddDisposition,
    ApprovalStatus,
    CharacterMemoryValidationError,
    EvidenceType,
    ExpiryKind,
    FactType,
    MemoryStatus,
    MemoryStore,
    add_or_merge_memory,
    approve_memory,
    create_evidence,
    create_memory,
    deserialize_memory_store,
    rollback_memory,
    select_prompt_eligible_memories,
    serialize_memory_store,
    validate_memory_store,
)


ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "core" / "character_memory_v2"
T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"
T2 = "2026-07-16T00:02:00Z"
ALLOWED_PREFIXES = (
    "core/character_memory_v2/",
    "tests/unit/test_character_memory_v2.py",
    "tests/integration/lcr_batch2_character_memory_v2_integration_test.py",
    "ntpe_lcr_batch2_character_memory_v2_test.py",
    "audits/legacy_capability_recovery/batch2/",
)
FROZEN_PREFIXES = (
    "ntpe_production_translate.py", "core/production_runtime/", "core/translation_runtime/",
    "core/translation_scheduler/", "core/translation_reliability/", "core/ai_provider/",
    "core/prompt_builder/", "core/prompt_compiler/", "core/quality/", "core/translation_quality_v5/",
    "core/translation_intelligence_corpus/", "artifacts/tic_batch", "docs/translation_intelligence/",
    "core/translation_discipline/", "core/translation_naturalness/",
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence(index: int, kind: str = "source_observation", excerpt: str | None = None):
    text = excerpt or f"人物證據 {index}"
    return create_evidence(
        evidence_type=kind,
        source_case_id=f"case-{index:03d}",
        source_segment_id=f"seg-{index:03d}",
        source_text_hash=sha(text),
        excerpt=text,
        language="ko",
        observed_at=T0,
    )


def memory(index: int, *, value: str | None = None, kind: str = "source_observation", character_id: str | None = None, fact_type: str = "other", confidence: float = 0.95):
    ev = evidence(index, kind, value)
    return create_memory(
        character_id=character_id or f"char-{index:03d}",
        fact_type=fact_type,
        value=value or f"人物事實 {index}",
        evidence=ev,
        confidence=confidence,
        created_at=T0,
    )


def changed_paths() -> list[str]:
    output = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT,
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    return [line[3:].strip().strip('"').replace("\\", "/") for line in output.splitlines() if line.strip()]


def tracked_diff_paths() -> list[str]:
    output = subprocess.run(
        ["git", "diff", "--name-only", "--"], cwd=ROOT,
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def benchmark() -> dict[str, float]:
    store = MemoryStore()
    start = time.perf_counter()
    for index in range(100):
        add_or_merge_memory(store, memory(index), now=T0)
    add_ms = (time.perf_counter() - start) * 1000

    duplicate = memory(0)
    start = time.perf_counter()
    for _ in range(100):
        result = add_or_merge_memory(store, duplicate, now=T1)
        assert result.disposition == AddDisposition.DUPLICATE
    dedup_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    selected = select_prompt_eligible_memories(store, token_budget=256, now=T1)
    selection_ms = (time.perf_counter() - start) * 1000
    assert selected.estimated_tokens <= 256

    start = time.perf_counter()
    encoded = serialize_memory_store(store)
    restored = deserialize_memory_store(encoded)
    assert serialize_memory_store(restored) == encoded
    serialization_ms = (time.perf_counter() - start) * 1000

    rollback_store = MemoryStore()
    original = memory(200, value="可回退事實", character_id="char-rollback")
    update = create_memory(
        character_id="char-rollback", fact_type="other", value="可回退事實",
        evidence=evidence(201, excerpt="第二份可追溯證據"), confidence=0.99, created_at=T0,
    )
    add_or_merge_memory(rollback_store, original, now=T0)
    add_or_merge_memory(rollback_store, update, now=T1)
    start = time.perf_counter()
    rollback_memory(rollback_store, original.memory_id, rolled_back_at=T2)
    rollback_ms = (time.perf_counter() - start) * 1000

    return {
        "add_merge_100_ms": round(add_ms, 3),
        "dedup_100_ms": round(dedup_ms, 3),
        "selection_100_ms": round(selection_ms, 3),
        "serialization_round_trip_100_ms": round(serialization_ms, 3),
        "rollback_ms": round(rollback_ms, 3),
    }


def run_checks() -> dict[str, object]:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append((name, bool(passed), detail))

    observed = memory(1, value="直接觀察", fact_type="role_or_identity")
    inferred = memory(2, value="規則推論", kind="ai_inference", fact_type="personality_trait", confidence=0.99)
    check("model-required-fields", len(observed.to_dict()) >= 17)
    check("evidence-separation", observed.evidence_type != inferred.evidence_type)
    check("confidence-not-approval", inferred.approval_status == ApprovalStatus.PENDING)
    check("stable-memory-id", memory(1, value="直接觀察", fact_type="role_or_identity").memory_id == observed.memory_id)

    store = MemoryStore()
    check("add-accepted", add_or_merge_memory(store, observed, now=T0).disposition == AddDisposition.ACCEPTED)
    check("exact-dedup", add_or_merge_memory(store, observed, now=T1).disposition == AddDisposition.DUPLICATE and len(store.records) == 1)
    add_or_merge_memory(store, inferred, now=T1)
    selected = select_prompt_eligible_memories(store, token_budget=256, now=T2)
    check("ai-default-ineligible", all(item.memory_id != inferred.memory_id for item in selected.items))
    approved = approve_memory(store, observed.memory_id, approved_at=T2, reviewer="human", decision_reference="decision-root")
    check("human-approved-priority", approved.approval_status == ApprovalStatus.APPROVED and approved.evidence_type == EvidenceType.HUMAN_APPROVED)
    check("prompt-budget", select_prompt_eligible_memories(store, token_budget=8, now="2026-07-16T00:03:00Z").estimated_tokens <= 8)
    check("zero-budget", not select_prompt_eligible_memories(store, token_budget=0, now=T2).items)

    temporal = memory(3, value="當下狀態", fact_type="temporal_state")
    check("temporal-expiry-safe-default", temporal.expiry_policy.kind != ExpiryKind.NEVER)

    merge_store = MemoryStore()
    first = memory(10, value="同一事實", character_id="char-merge")
    second = create_memory(
        character_id="char-merge", fact_type="other", value="同一事實",
        evidence=evidence(11, excerpt="第二證據"), confidence=0.99, created_at=T0,
    )
    add_or_merge_memory(merge_store, first, now=T0)
    check("evidence-merge", add_or_merge_memory(merge_store, second, now=T1).disposition == AddDisposition.MERGED)
    rolled = rollback_memory(merge_store, first.memory_id, rolled_back_at=T2)
    check("rollback-verifiable", rolled.version == 3 and len(rolled.evidence) == 2)

    conflict_store = MemoryStore()
    add_or_merge_memory(conflict_store, memory(20, value="值甲", character_id="char-conflict"), now=T0)
    conflict = add_or_merge_memory(conflict_store, memory(21, value="值乙", character_id="char-conflict"), now=T1)
    check("conflict-visible", conflict.disposition == AddDisposition.CONFLICT and bool(conflict.conflict and conflict.conflict.unresolved))
    check("conflict-fail-closed", not select_prompt_eligible_memories(conflict_store, now=T2).items)

    raw = serialize_memory_store(store)
    check("serialization-deterministic", serialize_memory_store(deserialize_memory_store(raw)) == raw)
    check("store-valid", validate_memory_store(store)["valid"])
    try:
        create_memory(character_id="char-x", fact_type="other", value="Author" + "ization: populated-token-value", evidence=evidence(30), confidence=0.9, created_at=T0)
        secret_rejected = False
    except CharacterMemoryValidationError:
        secret_rejected = True
    check("secret-like-input-rejected", secret_rejected)

    imports: list[str] = []
    for path in MODULE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    forbidden_imports = [name for name in imports if any(token in name for token in ("requests", "httpx", "socket", "openai", "ai_provider", "translation_runtime", "prompt_builder", "translation_intelligence_corpus"))]
    check("offline-dependency-boundary", not forbidden_imports, str(forbidden_imports))

    paths = changed_paths()
    disallowed = [path for path in paths if not any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)]
    check("git-allowlist", not disallowed, str(disallowed))
    frozen_changes = [path for path in tracked_diff_paths() if path.startswith(FROZEN_PREFIXES)]
    check("frozen-boundary", not frozen_changes, str(frozen_changes))
    deleted = subprocess.run(["git", "ls-files", "--deleted"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    check("tracked-deletions-zero", not deleted)

    performance = benchmark()
    check("performance-add-merge", performance["add_merge_100_ms"] < 100, str(performance["add_merge_100_ms"]))
    check("performance-selection", performance["selection_100_ms"] < 20, str(performance["selection_100_ms"]))
    check("performance-serialization", performance["serialization_round_trip_100_ms"] < 50, str(performance["serialization_round_trip_100_ms"]))

    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    failures = [name for name, passed, _ in checks if not passed]
    if failures:
        raise AssertionError("failed checks: " + ", ".join(failures))
    return {
        "checks": len(checks),
        "performance": performance,
        "changed_paths": paths,
        "provider_executed": False,
        "network_requests": 0,
        "new_translation_generated": False,
        "production_integration": False,
        "prompt_integration": False,
    }


def main() -> int:
    report = run_checks()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
