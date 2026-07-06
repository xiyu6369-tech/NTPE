from core.workflow.review_approval_layer import ReviewApprovalLayer
from core.workflow.review_gate import ApprovalGatePolicy
from core.workflow.review_state import ReviewState


def test_review_task_approval_flow():
    layer = ReviewApprovalLayer()
    task = layer.create_task("r1")
    assert task.state == ReviewState.PENDING
    layer.start("r1", reviewer="qa")
    layer.approve("r1", author="qa")
    result = layer.evaluate("r1")
    assert result.approved is True


def test_review_gate_quality_threshold():
    layer = ReviewApprovalLayer(ApprovalGatePolicy(minimum_quality_score=90.0))
    layer.create_task("r2")
    layer.approve("r2")
    result = layer.evaluate("r2", quality_score=80.0)
    assert result.approved is False
    assert result.reason == "quality_score_below_threshold"
