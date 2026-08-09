# =====================================================
# NTPE RM-7.3.2 P4 — Entity Consistency Review Canary
# =====================================================
"""Run RM-7.3.2 P4 Entity Consistency Review Validation.

Validates the complete review loop:
    EntityMismatch (from actual translation)
        ↓
    ReviewCandidate (with Evidence)
        ↓
    Deduplication (deterministic candidate_id)
        ↓
    Review ACCEPT → KnowledgeEvolutionCandidate
    Review REJECT → No Knowledge Evolution

Uses actual novel translation from RM-7.3.1 canary as evidence source.
No provider. No network. No auto-learning.
"""
from __future__ import annotations

import json
import sys
import io
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from core.entity_consistency import (
    ConsistencyChecker,
    EntityMismatch,
    create_matching_policy,
    FormAwareMatchingPolicy,
)
from core.entity_consistency.models import EntityType, Severity
from core.entity_review import (
    create_candidates_from_mismatches,
    get_global_store,
    get_review_engine,
    KnowledgeEvolutionExporter,
    ReviewReportExporter,
    ReviewStatus,
    reset_review_engine,
    set_global_store,
)
from core.knowledge_evolution.manager import KnowledgeManager
from core.knowledge_evolution.models import CandidateStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Test Translation Output (simulated from actual novel chunk 1)
# Using Chinese translation that would contain mismatches
# ----------------------------------------------------------------------

TRANSLATION_WITH_MISMATCHES = """第一章 — 初次見面

冬雨敲打著窗戶。鄭泰義望著窗外朦朧可見的路燈陷入沉思。那天好像與別的日子不同。並不是說有什麼不同的預感，而是因為結果那天一切都變了。

下午三點左右，泰義坐在一家普通的咖啡廳。名字叫「星咖啡」，咖啡價格稍貴但氣氛不錯。喝了兩口美式咖啡時，有人站在他的桌子前。

"鄭泰義先生嗎？"

抬頭看見一位穿著白色冬裙的年輕女子站在他面前。泰義緊張了。他從未把私人行程告訴過別人。

"是的，不過... 等等，妳怎麼知道我的名字？"

"重要的是不是我。" 她坐下時把手裡的信封推到桌上。"請看看這個。關於新林洞事件。"

鄭泰義的表情瞬間僵硬。聽到新林洞事件，他心底揮之不去的是無法洗刷的遺憾。那件事後他被迫辭職，在警方內部審計中背負了明顯的冤名。

"還有人提起那件事啊。" 泰義不悅地笑了。"三年前就結束的事了。"

"沒結束，泰義刑警。" 女子斬釘截鐵地說。"共犯者還在經理室自由工作，妳不可能不知道。"

泰義心裡浮現出久遠的疑問。新林洞事件當時，現場發現的會計帳本明明有兩本。但官方調查記錄只記載了一本。有人藏起了另一本帳本。

"妳也是警察嗎？"

"不。我只是個適應這種事的人。" 她動作要起身。"這不是禮物，是自爆。不知道我能等多久。"

泰義突然抓住一個閃現的記憶。"別撒謊。是導演派妳來的嗎？"

她微笑著站起身。"也許吧。但這種事總是一個人做不成的。"

他剛想再說什麼，咖啡廳外傳來警笛聲。兩輛警車堵住了巷口。女子趕緊從後門消失，動作快如影子。

"到這裡為止了嗎。" 泰義自語。"如果是這樣結束的話……"

但他錯了。這只是開始。

---

第二天早上，泰義搭乘地鐵3號線前往匿名委託人指定的地點。會議在首爾一棟廢棄商場地下室舉行。桌上放著三個舊紙箱。

"鄭先生，終於來了。"

聲音是個陌生的中年男子。他戴著深色眼鏡穿著黑西裝。泰義理所當然不知道這人的身份。但他散發的沉重氣場不是普通人的。

"這是什麼意思？為什麼叫我來這裡？"

"簡單。" 男子回答。"你必須在三本書中選一本。這三項工作中只有一項是真相，其餘是假的。

第一箱裝滿舊文件。第一箱有新林洞大樓圖面，第二箱有通往香港的未完成法人文件，第三箱有意味深長的紅外線照片。

"我還有多少時間？"

"5分鐘。不決定就按指示處理。"

泰義深吸一口氣審視文件。警察時代每逢此時他的感覺格外敏銳。他最信任的人是妻子柳莉。但柳莉現在也不在他身邊。那是舊傷。

"第一箱。這是真的。"

中年男子笑了。"選得不錯。現在是第二個問題。"

他話還沒說完，泰義打斷道。"還沒。我有話要先說。"

"什麼事？"

"新林洞事件我要先佔有。這樣我們會議就結束了。"

瞬間，地下室燈全滅了。黑暗中傳來沉重腳步聲。泰義本能地站起貼牆。他的手記得久違的手槍感覺。

燈再亮時，中年男子不見了。桌上只剩一張小便條。紙上寫著幾個字。

"最後任務是活著回來。 — Y"

泰義額頭冒出冷汗。這簽名，還有那開頭。他意識到這一切是個巨大陷阱。但現在無法回頭。他選的路是生死真相的走鋼索。

喝口咖啡，泰義低聲說。

"好，幹一票。"
"""

# Expected canonical forms from RM-7.3.1 canary
EXPECTED_FORMS = {
    "정태의": "鄭泰義",      # FULL_NAME
    "태의": "泰義",        # GIVEN_NAME
    "정 씨": "鄭先生",      # FORMAL (family + honorific)
    "태의야": "泰義啊",     # INTIMATE (given + suffix)
}

# Entity ID mapping
ENTITY_ID_MAP = {
    "정태의": "character_jeong_taeui",
    "태의": "character_jeong_taeui",
    "정 씨": "character_jeong_taeui",
    "태의야": "character_jeong_taeui",
}


def build_matching_policy() -> FormAwareMatchingPolicy:
    """Build the form-aware matching policy for the test entity."""
    return create_matching_policy(
        full_name="鄭泰義",
        given_name="泰義",
        family_name="鄭",
        formal="鄭先生",
        intimate="泰義啊",
    )


def run_consistency_check(translation: str, policy: FormAwareMatchingPolicy) -> list:
    """Run consistency checker and return mismatches."""
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    # Knowledge entries for the test entity
    knowledge_entries = [
        {"source": "정태의", "canonical": "鄭泰義", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
        {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
        {"source": "정 씨", "canonical": "鄭先生", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
        {"source": "태의야", "canonical": "泰義啊", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    
    checker.check_entries_form_aware(knowledge_entries, translation)
    return checker.mismatches


def test_case_a_true_mismatch():
    """Case A: True mismatch — GIVEN_NAME expected '泰義' but found '鄭泰義'."""
    print("\n" + "=" * 60)
    print("  CASE A: True Mismatch — GIVEN_NAME expansion")
    print("=" * 60)
    
    # Create a translation where 泰義 appears as 鄭泰義 (full name expansion)
    # In the actual translation, "泰義" appears standalone correctly
    # But we simulate a mismatch for testing
    translation = "泰義坐在咖啡廳。"  # Correct: 泰義
    translation_bad = "鄭泰義坐在咖啡廳。"  # Wrong: full name expansion
    
    policy = build_matching_policy()
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    # Check the BAD translation
    knowledge_entries = [
        {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    checker.check_entries_form_aware(knowledge_entries, translation_bad)
    
    mismatches = checker.mismatches
    print(f"  Mismatches found: {len(mismatches)}")
    for m in mismatches:
        print(f"    Source: {m.source}")
        print(f"    Expected: {m.expected}")
        print(f"    Found: {m.found}")
        print(f"    Severity: {m.severity.value}")
        print(f"    Form Type: GIVEN_NAME")
    
    # Create candidates
    candidates = create_candidates_from_mismatches(
        mismatches=mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=translation_bad,
        matching_policy=policy,
    )
    
    print(f"\n  Candidates created: {len(candidates)}")
    for c in candidates:
        print(f"    Candidate ID: {c.candidate_id}")
        print(f"    Entity ID: {c.entity_id}")
        print(f"    Form Type: {c.form_type.value}")
        print(f"    Expected: {c.expected_translation}")
        print(f"    Actual: {c.actual_translation}")
        print(f"    Evidence Rule: {c.evidence.rule}")
        print(f"    Status: {c.status.value}")
    
    assert len(candidates) == 1, "Should create exactly 1 candidate"
    assert candidates[0].form_type.value == "GIVEN_NAME"
    assert candidates[0].expected_translation == "泰義"
    assert candidates[0].actual_translation == "鄭泰義"
    assert "GIVEN_NAME_FORBIDS" in candidates[0].evidence.rule
    assert candidates[0].status == ReviewStatus.OPEN
    
    print("  ✓ CASE A PASSED")
    return candidates[0]


def test_case_b_legal_formal():
    """Case B: Legal FORMAL — both '鄭先生' and '鄭泰義先生' should MATCH."""
    print("\n" + "=" * 60)
    print("  CASE B: Legal FORMAL — both patterns allowed")
    print("=" * 60)
    
    # Both formal forms should be accepted
    translation1 = "鄭先生看著窗外。"      # family + honorific
    translation2 = "鄭泰義先生看著窗外。"  # full + honorific
    
    policy = build_matching_policy()
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    knowledge_entries = [
        {"source": "정 씨", "canonical": "鄭先生", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    
    # Test translation1
    checker.clear()
    checker.check_entries_form_aware(knowledge_entries, translation1)
    print(f"  Translation: '{translation1}'")
    print(f"  Matches: {checker.pass_count}, Mismatches: {checker.mismatch_count}")
    assert checker.mismatch_count == 0, "鄭先生 should MATCH"
    
    # Test translation2
    checker.clear()
    checker.set_form_policy(policy)
    checker.check_entries_form_aware(knowledge_entries, translation2)
    print(f"  Translation: '{translation2}'")
    print(f"  Matches: {checker.pass_count}, Mismatches: {checker.mismatch_count}")
    assert checker.mismatch_count == 0, "鄭泰義先生 should MATCH"
    
    print("  ✓ CASE B PASSED")
    return True


def test_case_c_legal_intimate():
    """Case C: Legal INTIMATE — '泰義啊' should MATCH, '鄭泰義啊' should NOT."""
    print("\n" + "=" * 60)
    print("  CASE C: Legal INTIMATE — only given+suffix allowed")
    print("=" * 60)
    
    translation_correct = "泰義啊！"  # Correct: given + intimate suffix
    translation_wrong = "鄭泰義啊！"   # Wrong: full + intimate suffix
    
    policy = build_matching_policy()
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    knowledge_entries = [
        {"source": "태의야", "canonical": "泰義啊", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    
    # Test correct
    checker.clear()
    checker.set_form_policy(policy)
    checker.check_entries_form_aware(knowledge_entries, translation_correct)
    print(f"  Translation: '{translation_correct}'")
    print(f"  Matches: {checker.pass_count}, Mismatches: {checker.mismatch_count}")
    assert checker.mismatch_count == 0, "泰義啊 should MATCH"
    
    # Test wrong (should be MISMATCH)
    checker.clear()
    checker.set_form_policy(policy)
    checker.check_entries_form_aware(knowledge_entries, translation_wrong)
    print(f"  Translation: '{translation_wrong}'")
    print(f"  Matches: {checker.pass_count}, Mismatches: {checker.mismatch_count}")
    assert checker.mismatch_count == 1, "鄭泰義啊 should MISMATCH"
    
    mismatches = checker.mismatches
    print(f"  Mismatch: expected={mismatches[0].expected}, found={mismatches[0].found}")
    assert "INTIMATE_ONLY_GIVEN_PLUS_SUFFIX" in mismatches[0].metadata.get("match_rule", "")
    
    print("  ✓ CASE C PASSED")
    return True


def test_deduplication():
    """Test deterministic deduplication — same evidence = same candidate_id."""
    print("\n" + "=" * 60)
    print("  TEST: Deterministic Deduplication")
    print("=" * 60)
    
    policy = build_matching_policy()
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    # Same mismatch twice
    translation_bad = "鄭泰義坐在咖啡廳。"
    knowledge_entries = [
        {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    
    # Run 1
    checker.clear()
    checker.set_form_policy(policy)
    checker.check_entries_form_aware(knowledge_entries, translation_bad)
    candidates1 = create_candidates_from_mismatches(
        mismatches=checker.mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=translation_bad,
        matching_policy=policy,
    )
    
    # Run 2 (simulate re-running on same text)
    checker.clear()
    checker.set_form_policy(policy)
    checker.check_entries_form_aware(knowledge_entries, translation_bad)
    candidates2 = create_candidates_from_mismatches(
        mismatches=checker.mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=translation_bad,
        matching_policy=policy,
    )
    
    print(f"  Run 1 Candidate ID: {candidates1[0].candidate_id}")
    print(f"  Run 2 Candidate ID: {candidates2[0].candidate_id}")
    
    assert candidates1[0].candidate_id == candidates2[0].candidate_id, \
        "Same evidence must produce same candidate_id"
    
    # Test deduplicator
    set_global_store(None)  # Reset global store
    store = get_global_store()
    
    store.add(candidates1[0])
    store.add(candidates2[0])
    
    open_candidates = store.list_open()
    print(f"  After adding both: {len(open_candidates)} OPEN candidates")
    assert len(open_candidates) == 1, "Deduplication should keep only 1"
    
    print("  ✓ DEDUPLICATION PASSED")
    return True


def test_review_lifecycle():
    """Test complete review lifecycle: OPEN → ACCEPT → KE Candidate, OPEN → REJECT → No KE."""
    print("\n" + "=" * 60)
    print("  TEST: Review Lifecycle")
    print("=" * 60)
    
    set_global_store(None)
    reset_review_engine()
    
    policy = build_matching_policy()
    checker = ConsistencyChecker()
    checker.set_form_policy(policy)
    
    # Create a mismatch
    translation_bad = "鄭泰義坐在咖啡廳。"  # GIVEN_NAME expansion
    knowledge_entries = [
        {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    checker.check_entries_form_aware(knowledge_entries, translation_bad)
    
    candidates = create_candidates_from_mismatches(
        mismatches=checker.mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=translation_bad,
        matching_policy=policy,
    )
    
    candidate = candidates[0]
    candidate_id = candidate.candidate_id
    
    # Add to store
    store = get_global_store()
    store.add(candidate)
    
    # Get review engine
    engine = get_review_engine()
    
    # Test ACCEPT path
    print("  Testing ACCEPT path...")
    ke_candidate = engine.accept(candidate_id, reviewer="test_user", reason="True mismatch, needs learning")
    
    print(f"    KE Candidate created: {ke_candidate.source_candidate_id}")
    print(f"    Entity ID: {ke_candidate.entity_id}")
    print(f"    Expected: {ke_candidate.expected_translation}")
    print(f"    Provenance: {ke_candidate.provenance}")
    
    assert ke_candidate.source_candidate_id == candidate_id
    assert ke_candidate.provenance["source"] == "ENTITY_CONSISTENCY"
    assert ke_candidate.provenance["review_status"] == "ACCEPTED"
    
    # Verify candidate status updated
    updated = engine.get_candidate(candidate_id)
    assert updated.status == ReviewStatus.ACCEPTED
    
    # Test REJECT path (create another candidate)
    print("  Testing REJECT path...")
    translation_bad2 = "鄭泰義啊！"  # INTIMATE expansion
    checker.clear()
    checker.set_form_policy(policy)
    knowledge_entries2 = [
        {"source": "태의야", "canonical": "泰義啊", "entity_type": "CHARACTER", "entity_id": "character_jeong_taeui"},
    ]
    checker.check_entries_form_aware(knowledge_entries2, translation_bad2)
    
    candidates2 = create_candidates_from_mismatches(
        mismatches=checker.mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=translation_bad2,
        matching_policy=policy,
    )
    
    candidate2 = candidates2[0]
    candidate2_id = candidate2.candidate_id
    store.add(candidate2)
    
    rejected = engine.reject(candidate2_id, reviewer="test_user", reason="Contextual exception, deliberate variant")
    
    print(f"    Rejected candidate: {rejected.candidate_id}")
    print(f"    Status: {rejected.status.value}")
    
    assert rejected.status == ReviewStatus.REJECTED
    
    # Verify NO KnowledgeEvolutionCandidate created for rejected
    ke_candidates = engine.get_accepted_ke_candidates()
    assert len(ke_candidates) == 1, "Only ACCEPTED should create KE candidate"
    assert ke_candidates[0].source_candidate_id == candidate_id
    
    print("  ✓ REVIEW LIFECYCLE PASSED")
    return True


def test_knowledge_evolution_bridge():
    """Test export to Knowledge Evolution pipeline."""
    print("\n" + "=" * 60)
    print("  TEST: Knowledge Evolution Bridge")
    print("=" * 60)
    
    km = KnowledgeManager()
    exporter = KnowledgeEvolutionExporter(knowledge_manager=km)
    
    # Export accepted candidates
    learning_candidates = exporter.export_accepted()
    
    print(f"  Exported LearningCandidates: {len(learning_candidates)}")
    for lc in learning_candidates:
        print(f"    Source: {lc.source}")
        print(f"    Canonical: {lc.canonical}")
        print(f"    Entity Type: {lc.entity_type.value}")
        print(f"    Confidence: {lc.confidence}")
        print(f"    Context Hints: {lc.context_hints}")
        print(f"    Status: {lc.status.value}")
    
    assert len(learning_candidates) == 1, "Should export 1 learning candidate"
    lc = learning_candidates[0]
    assert lc.source == "character_jeong_taeui"
    assert lc.canonical == "泰義"
    assert lc.entity_type.value == "CHARACTER"
    assert "ENTITY_CONSISTENCY" in str(lc.context_hints)
    
    # Verify no auto-promotion (status should be PENDING)
    assert lc.status == CandidateStatus.PENDING
    
    print("  ✓ KNOWLEDGE EVOLUTION BRIDGE PASSED")
    return True


def test_full_canary_with_actual_translation():
    """Run full canary using the actual novel translation."""
    print("\n" + "=" * 60)
    print("  FULL CANARY: Actual Novel Translation")
    print("=" * 60)
    
    set_global_store(None)
    reset_review_engine()
    
    policy = build_matching_policy()
    mismatches = run_consistency_check(TRANSLATION_WITH_MISMATCHES, policy)
    
    print(f"  Total mismatches in translation: {len(mismatches)}")
    for m in mismatches:
        print(f"    [{m.severity.value}] {m.entity_type.value}: expected='{m.expected}' found='{m.found}' source='{m.source}'")
    
    # Create candidates
    candidates = create_candidates_from_mismatches(
        mismatches=mismatches,
        entity_id_map=ENTITY_ID_MAP,
        source_chunk=TRANSLATION_WITH_MISMATCHES[:500],
        matching_policy=policy,
    )
    
    print(f"\n  Candidates created: {len(candidates)}")
    for c in candidates:
        print(f"    [{c.candidate_id}] {c.form_type.value}: {c.expected_translation} → {c.actual_translation}")
    
    # Add to store
    store = get_global_store()
    for c in candidates:
        store.add(c)
    
    # Review all
    engine = get_review_engine()
    for c in candidates:
        if c.form_type.value == "GIVEN_NAME" and "GIVEN_NAME_FORBIDS" in c.evidence.rule:
            # This is a true mismatch - ACCEPT
            ke = engine.accept(c.candidate_id, reviewer="canary", reason="True form violation")
            print(f"  ACCEPTED: {c.candidate_id} → KE Candidate")
        else:
            # Others - REJECT as contextual/allowed
            engine.reject(c.candidate_id, reviewer="canary", reason="Contextual variant allowed")
            print(f"  REJECTED: {c.candidate_id}")
    
    # Export to KE
    exporter = KnowledgeEvolutionExporter(knowledge_manager=KnowledgeManager(), review_engine=engine)
    ke_candidates = exporter.export_accepted()
    
    print(f"\n  Knowledge Evolution Candidates: {len(ke_candidates)}")
    
    # Stats
    stats = engine.stats()
    print(f"\n  Review Stats: {stats}")
    
    # Export report
    reporter = ReviewReportExporter(engine)
    report_md = reporter.to_markdown()
    print("\n  Report generated successfully")
    
    print("  ✓ FULL CANARY PASSED")
    return True


def main() -> int:
    print("=" * 60)
    print("  RM-7.3.2 P4 Entity Consistency Review Canary")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Core test cases
        test_case_a_true_mismatch()
        test_case_b_legal_formal()
        test_case_c_legal_intimate()
        test_deduplication()
        test_review_lifecycle()
        test_knowledge_evolution_bridge()
        test_full_canary_with_actual_translation()
        
        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n  ✗ ASSERTION FAILED: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n  ✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    return 1 if not all_passed else 0


if __name__ == "__main__":
    sys.exit(main())