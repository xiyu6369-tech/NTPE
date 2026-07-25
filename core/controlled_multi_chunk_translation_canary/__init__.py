"""Stage 7.4 controlled sequential three-chunk literary canary."""

from .checkpoint import read_checkpoint, write_checkpoint_atomic
from .errors import (
    ControlledMultiChunkAuthorityError, ControlledMultiChunkCheckpointError,
    ControlledMultiChunkError, ControlledMultiChunkOutputError,
    ControlledMultiChunkProviderError, ControlledMultiChunkQualityError,
    ControlledMultiChunkResolutionError, ControlledMultiChunkVerificationError,
)
from .executor import ControlledMultiChunkExecutor
from .models import (
    CheckpointRecord, ChunkCompletionEvidence, ChunkExecutionPlan,
    MultiChunkCanaryRequest, MultiChunkResult, MultiChunkVerificationResult,
)
from .resolver import (
    ResolvedMultiChunkSource, build_multi_chunk_request,
    resolve_multi_chunk_source,
)
from .verification import verify_multi_chunk_result

__all__ = [
    "MultiChunkCanaryRequest",
    "ChunkExecutionPlan",
    "ChunkCompletionEvidence",
    "CheckpointRecord",
    "MultiChunkResult",
    "MultiChunkVerificationResult",
    "ResolvedMultiChunkSource",
    "ControlledMultiChunkExecutor",
    "resolve_multi_chunk_source",
    "build_multi_chunk_request",
    "write_checkpoint_atomic",
    "read_checkpoint",
    "verify_multi_chunk_result",
    "ControlledMultiChunkError",
    "ControlledMultiChunkAuthorityError",
    "ControlledMultiChunkResolutionError",
    "ControlledMultiChunkProviderError",
    "ControlledMultiChunkQualityError",
    "ControlledMultiChunkCheckpointError",
    "ControlledMultiChunkOutputError",
    "ControlledMultiChunkVerificationError",
]
