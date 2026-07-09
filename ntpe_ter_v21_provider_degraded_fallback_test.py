from lts.txt_translation_runtime import is_retryable_error, _is_provider_degraded_error, _provider_model_chain

print('NTPE TER-v2.1 Provider Degraded Fallback Test')
print('=' * 48)
err = "NVIDIA API error 400: DEGRADED function cannot be invoked"
assert is_retryable_error(err)
assert _is_provider_degraded_error(err)
chain = _provider_model_chain('meta/llama-3.3-70b-instruct')
assert chain[0] == 'meta/llama-3.3-70b-instruct'
print('Degraded Retryable        PASS')
print('Degraded Detector         PASS')
print('Model Chain               PASS')
print('PASS')
