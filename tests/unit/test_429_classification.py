from core.translation_engine.provider_runtime import is_retryable_translation_provider_error, RETRYABLE_PROVIDER_ERROR_PATTERNS

error = 'NVIDIA API error 429: {"status":429,"title":"Too Many Requests"}'
print('Error:', error)
print('Patterns:', RETRYABLE_PROVIDER_ERROR_PATTERNS)
print('Retryable:', is_retryable_translation_provider_error(error))

# Also test the exact error from logs
error2 = 'NVIDIA API error 429: {"status":429,"title":"Too Many Requests"}'
print('Error2:', error2)
print('Retryable2:', is_retryable_translation_provider_error(error2))