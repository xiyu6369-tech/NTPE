from core.workflow.review_approval_layer import ReviewApprovalLayer
from core.workflow.review_gate import ApprovalGatePolicy
from core.workflow.review_metrics import build_review_metrics
from core.workflow.review_state import ReviewState


def main() -> int:
    layer = ReviewApprovalLayer(ApprovalGatePolicy(minimum_quality_score=90.0))
    task = layer.create_task("review-1", workflow_id="wf-1", target_id="chapter-1")
    assert task.state == ReviewState.PENDING
    layer.start("review-1", reviewer="editor")
    layer.approve("review-1", author="editor")
    result = layer.evaluate("review-1", quality_score=95.0)
    assert result.approved is True
    metrics = build_review_metrics(layer.registry.all())
    assert metrics["approved"] == 1
    print("Stage-17.4 Review Approval Layer PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
