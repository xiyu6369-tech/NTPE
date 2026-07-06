from core.workflow.review_bridge import evaluate_review_gate


def test_review_bridge_blocks_unapproved_task():
    result = evaluate_review_gate("bridge-r1", approved=False)
    assert result.approved is False


def test_review_bridge_allows_approved_task():
    result = evaluate_review_gate("bridge-r2", approved=True)
    assert result.approved is True
