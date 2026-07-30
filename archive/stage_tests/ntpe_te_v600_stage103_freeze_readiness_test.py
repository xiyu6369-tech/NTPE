from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from core.translation_discipline import evaluate_freeze_readiness


def _write_audit(root: Path, chunk: int, action: str, used: int = 0) -> None:
    payload = {
        "final_action": action,
        "quality": {"issues": []},
        "adaptive_retry_policy": {
            "retry_tier": "none",
            "provider_call_budget": {"limit": 2, "used": used, "remaining": 2-used},
        },
        "local_repair": {"changed": False},
    }
    (root / f"original_ko_chunk_{chunk:06d}_discipline_audit_attempt_1.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_quality(root: Path, chunk: int) -> None:
    payload={"accepted": True, "decision": "accepted", "merged_issues": []}
    (root / f"original_ko_chunk_{chunk:06d}_quality_v5_attempt_1.json").write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    with TemporaryDirectory() as tmp:
        base=Path(tmp)/"base"; cur=Path(tmp)/"cur"; base.mkdir(); cur.mkdir()
        for i in range(1, 6): _write_quality(base, i); _write_audit(cur, i, "accept", used=0)
        ok=evaluate_freeze_readiness(base, cur, expected_chunks=5)
        assert ok.ready and not ok.blockers
        (cur / "original_ko_chunk_000005_discipline_audit_attempt_1.json").unlink()
        bad=evaluate_freeze_readiness(base, cur, expected_chunks=5)
        assert not bad.ready and any("incomplete" in x for x in bad.blockers)
    print("TE v6.0 Stage 10.3 Freeze Readiness ALL PASS")

if __name__ == "__main__": main()
