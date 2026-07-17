import hashlib
import json
from pathlib import Path
import shutil

from core.lcr_production_shadow_hook.batch107_real_provider_validation import (
    PACKAGE_RELATIVE_PATH,
    execute_batch107,
    load_execution_package,
)
from tests.unit.test_lcr_batch107_real_provider_validation import (
    NOW,
    FakeProvider,
    PassedVerification,
    authorization,
)


ROOT = Path(__file__).resolve().parents[2]


def test_offline_authorized_single_chunk_sentinels_and_isolated_review(tmp_path):
    source = tmp_path / "artifacts/tic_batch2/TRANSLATION_CASES.json"
    source.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "artifacts/tic_batch2/TRANSLATION_CASES.json", source)
    sentinels = {}
    for name in ("formal_output", "resume", "production_cache", "character_store", "context_store"):
        path = tmp_path / f"{name}.sentinel"
        path.write_text(f"unchanged-{name}", encoding="utf-8")
        sentinels[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    item = load_execution_package(PACKAGE_RELATIVE_PATH, root=ROOT)
    provider = FakeProvider()
    result = execute_batch107(
        item, authorization=authorization(item), root=tmp_path, now=NOW,
        confirm_execution_id=str(item["execution_id"]), environ={"NVIDIA_API_KEY": "offline-test-only"},
        provider=provider, test_mode=True, semantic_verifier=lambda semantic_input: PassedVerification(),
    )
    assert result.outcome == "verified_candidate"
    assert result.provider_requests == result.network_requests == 2
    assert result.retry_count == 0 and result.fallback_used is False
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in sentinels.items())
    assert not result.formal_output_changed and not result.resume_changed
    assert not result.cache_changed and not result.stores_changed
    artifact = json.loads(Path(result.review_artifact_path).read_text(encoding="utf-8"))
    assert artifact["batch"] == "10.7" and artifact["manual_review_status"] == "awaiting_manual_review"
    assert artifact["formal_output_changed"] is False


def test_pre_execution_package_requires_no_credential_and_makes_no_provider_call():
    item = load_execution_package(PACKAGE_RELATIVE_PATH, root=ROOT)
    assert item["execution_status"] == "awaiting_user_authorization"
    assert item["provider_requests"] == item["network_requests"] == 0
    assert item["real_provider_execution_authorized"] is False

