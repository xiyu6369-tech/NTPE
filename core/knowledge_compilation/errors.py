"""
Knowledge Compilation Engine - Errors

定義知識編譯引擎中使用的異常類別。
"""

from __future__ import annotations


class CompilationError(Exception):
    """知識編譯過程中的基礎異常。"""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class InvalidEntityStateError(CompilationError):
    """實體狀態不符合編譯要求（非 APPROVED/AUTO_APPROVED）。"""
    
    def __init__(self, entity_id: str, entity_type: str, current_state: str, allowed_states: list[str]) -> None:
        message = f"實體 {entity_id} ({entity_type}) 狀態為 {current_state}，僅允許 {allowed_states}"
        details = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "current_state": current_state,
            "allowed_states": allowed_states,
        }
        super().__init__(message, details)


class EmptyPackageError(CompilationError):
    """編譯結果為空包。"""
    
    def __init__(self, message: str = "沒有符合條件的已核准實體可供編譯") -> None:
        super().__init__(message)


class ManifestGenerationError(CompilationError):
    """Manifest 產生失敗。"""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message, details)


class ChecksumCalculationError(CompilationError):
    """Checksum 計算失敗。"""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message, details)


class PackageBuildError(CompilationError):
    """套件建構失敗。"""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message, details)


class RuntimeInvocationError(CompilationError):
    """運行時嘗試調用編譯器（違反建構時/運行時邊界）。"""
    
    def __init__(self, message: str = "運行時環境禁止調用知識編譯器；請使用凍結套件讀取器") -> None:
        super().__init__(message)