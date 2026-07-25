"""Central Stage 7.3 controlled-canary policy."""

from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_translation_runtime_execution_request"
REQUEST_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_translation_runtime_execution_result"
RESULT_SCHEMA_VERSION = "1.0"
EVIDENCE_SCHEMA_NAME = "ntpe.controlled_translation_runtime_output_evidence"
EVIDENCE_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = "ntpe.controlled_translation_runtime_verification_result"
VERIFICATION_SCHEMA_VERSION = "1.0"

EXECUTION_INTENT = (
    "execute_exactly_one_authenticated_controlled_literary_translation_chunk_"
    "through_the_existing_ntpe_translation_runtime_and_provider_path"
)
TARGET_LANGUAGE = "zh-TW"
TRANSLATION_PROFILE = "literary"
PROVIDER = "nvidia"
PROVIDER_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
PROVIDER_MODEL = "meta/llama-3.3-70b-instruct"
PROVIDER_CREDENTIAL_ENV = "NVIDIA_API_KEY"
REAL_CANARY_GATE_ENV = "NTPE_STAGE73_REAL_PROVIDER_CANARY"
SOURCE_FIXTURE_ID = "ntpe-literary-smoke-set-original-ko-v1"
SOURCE_FIXTURE_PATH = "tests/literary/Smoke_Set/original_ko.txt"
SOURCE_FIXTURE_FINGERPRINT = (
    "5e35ad3aaff5214cd2b6da0f64fb4c099f540584a701d4afa65f29c460f64113"
)
SOURCE_CHARACTER_COUNT = 455
CHUNK_SIZE = 600
OUTPUT_ROOT = "artifacts/controlled_translation_runtime_stage73"
FIXED_NAMES = (("일레이", "伊萊"), ("정태의", "鄭泰義"))


@dataclass(frozen=True)
class ControlledTranslationExecutionPolicy:
    target_language: str = TARGET_LANGUAGE
    translation_profile: str = TRANSLATION_PROFILE
    unit_scope: int = 1
    source_count: int = 1
    chunk_count: int = 1
    provider_requests: int = 1
    provider_attempts: int = 1
    retries: int = 0
    fallbacks: int = 0
    automatic_rollouts: int = 0
    formal_output_replacements: int = 0
    resume_mutations: int = 0
    cache_mutations: int = 0
    upstream_chain_layers: int = 38
    result_chain_layers: int = 40
    evidence_chain_layers: int = 41
