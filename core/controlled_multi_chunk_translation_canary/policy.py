"""Frozen Stage 7.4 controlled multi-chunk canary policy."""

REQUEST_SCHEMA = "ntpe.controlled_multi_chunk_translation_request"
CHUNK_PLAN_SCHEMA = "ntpe.controlled_translation_chunk_plan"
CHUNK_EVIDENCE_SCHEMA = "ntpe.controlled_translation_chunk_evidence"
CHECKPOINT_SCHEMA = "ntpe.controlled_translation_checkpoint"
RESULT_SCHEMA = "ntpe.controlled_multi_chunk_translation_result"
VERIFICATION_SCHEMA = "ntpe.controlled_multi_chunk_translation_verification_result"
SCHEMA_VERSION = "1.0"

INTENT = (
    "translate_exactly_three_consecutive_authenticated_literary_chunks_"
    "sequentially_persist_each_successful_output_immediately_and_create_"
    "deterministic_checkpoints_without_formal_rollout"
)
SOURCE_FIXTURE_ID = "ntpe-stage74-golden-excerpt-ko-v1"
SOURCE_FIXTURE_PATH = (
    "tests/integration/controlled_multi_chunk_translation_canary/fixtures/"
    "stage74_original_ko.txt"
)
SOURCE_FINGERPRINT = (
    "53d96e78f7ce47c260185b55436844c1619a83d02c0feea11bef7793f28b9bea"
)
SOURCE_CHARACTER_COUNT = 1633
CHUNK_SIZE = 600
CHUNK_COUNT = 3
CHUNK_CHARACTER_COUNTS = (575, 540, 514)
CHUNK_FINGERPRINTS = (
    "5be537c45817ccc7aaf13de6c31fb4708c29a87e2e454949d60e33337feb726c",
    "542e4c34fccaac7a1a82692a584bc8a5203699d4b0821354387ba01807217dc2",
    "8527171c147f77e3715b3af9c040d9acf4b4318eb24b272d4051e363efff3791",
)
TARGET_LANGUAGE = "zh-TW"
PROFILE = "literary"
PROVIDER = "nvidia"
PROVIDER_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
PROVIDER_MODEL = "meta/llama-3.3-70b-instruct"
CREDENTIAL_ENV = "NVIDIA_API_KEY"
REAL_CANARY_GATE_ENV = "NTPE_STAGE74_REAL_PROVIDER_CANARY"
CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 180
REQUEST_CAP = 3
ATTEMPT_CAP = 3
OUTPUT_ROOT = "artifacts/controlled_multi_chunk_translation_stage74"
CONTEXT_LIMIT = 160
COMBINED_BOUNDARY = "\n\n"
FIXED_NAMES = (("일레이", "伊萊"), ("정태의", "鄭泰義"))
