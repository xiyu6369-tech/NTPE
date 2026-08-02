"""
Knowledge Review Workflow - Errors

定義知識審核工作流中使用的異常類別。
"""


class KnowledgeReviewError(Exception):
    """知識審核工作流基礎異常。"""
    pass


class InvalidStateTransition(KnowledgeReviewError):
    """無效的狀態轉換。"""

    def __init__(self, current_state: str, target_state: str, message: str = None):
        self.current_state = current_state
        self.target_state = target_state
        msg = message or f"無效的狀態轉換：{current_state} -> {target_state}"
        super().__init__(msg)


class InvalidReviewStateError(KnowledgeReviewError):
    """無效的審核狀態轉換。"""

    def __init__(self, current_state: str, target_state: str, message: str = None):
        self.current_state = current_state
        self.target_state = target_state
        msg = message or f"無效的狀態轉換：{current_state} -> {target_state}"
        super().__init__(msg)


class ReviewItemNotFoundError(KnowledgeReviewError):
    """找不到審核項目。"""

    def __init__(self, review_id: str):
        self.review_id = review_id
        super().__init__(f"找不到審核項目：{review_id}")


class DuplicateReviewItemError(KnowledgeReviewError):
    """重複的審核項目。"""

    def __init__(self, review_id: str):
        self.review_id = review_id
        super().__init__(f"審核項目已存在：{review_id}")


class InvalidConfidenceScoreError(KnowledgeReviewError):
    """無效的信心度分數。"""

    def __init__(self, score: float, message: str = None):
        self.score = score
        msg = message or f"無效的信心度分數：{score} (必須在 0.0 到 1.0 之間)"
        super().__init__(msg)


class ValidationFailedError(KnowledgeReviewError):
    """驗證失敗。"""

    def __init__(self, entity_type: str, entity_id: str, errors: list[str]):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.errors = errors
        super().__init__(
            f"驗證失敗 [{entity_type}:{entity_id}]：{'; '.join(errors)}"
        )


class AuditLogError(KnowledgeReviewError):
    """審計日誌錯誤。"""
    pass