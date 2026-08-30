"""Unit tests for provider retry/backoff behavior on 429 rate limit errors."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock

from core.ai_provider.retry import RetryPolicy
from core.ai_provider.execution_policy import ProviderRuntimeExecutionPolicy
from core.ai_provider.contracts import ProviderError, ProviderRequest, ProviderResponse
from core.translation_engine.provider_runtime import build_translation_provider_manager, TranslationProviderSettings
from core.translation_reliability.adaptive_retry_policy import AdaptiveRetryPolicy


class TestRetryPolicy429:
    """Test RetryPolicy behavior with 429 errors."""

    def test_retry_policy_max_attempts_default(self):
        """RetryPolicy defaults to 3 attempts."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3

    def test_retry_policy_base_delay_default(self):
        """RetryPolicy defaults to 0.0 base delay."""
        policy = RetryPolicy()
        assert policy.base_delay_seconds == 0.0

    def test_retry_policy_backoff_factor_default(self):
        """RetryPolicy defaults to 2.0 backoff factor."""
        policy = RetryPolicy()
        assert policy.backoff_factor == 2.0

    def test_retry_policy_custom_values(self):
        """RetryPolicy accepts custom values."""
        policy = RetryPolicy(max_attempts=5, base_delay_seconds=10.0, backoff_factor=1.5)
        assert policy.max_attempts == 5
        assert policy.base_delay_seconds == 10.0
        assert policy.backoff_factor == 1.5

    def test_retry_policy_run_success_on_first_attempt(self):
        """RetryPolicy.run succeeds on first attempt."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        mock_fn = Mock(return_value="success")
        result = policy.run(mock_fn)
        assert result == "success"
        assert mock_fn.call_count == 1

    def test_retry_policy_run_retries_on_retryable_error(self):
        """RetryPolicy.run retries on retryable ProviderError."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        mock_fn = Mock(side_effect=[
            ProviderError("rate limit", "nvidia", retryable=True),
            ProviderError("rate limit", "nvidia", retryable=True),
            "success"
        ])
        result = policy.run(mock_fn)
        assert result == "success"
        assert mock_fn.call_count == 3

    def test_retry_policy_run_exhausts_attempts(self):
        """RetryPolicy.run raises after max attempts exhausted."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        mock_fn = Mock(side_effect=ProviderError("rate limit", "nvidia", retryable=True))
        with pytest.raises(ProviderError):
            policy.run(mock_fn)
        assert mock_fn.call_count == 3

    def test_retry_policy_no_retry_on_non_retryable(self):
        """RetryPolicy.run does not retry on non-retryable error."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        mock_fn = Mock(side_effect=ProviderError("invalid request", "nvidia", retryable=False))
        with pytest.raises(ProviderError) as exc_info:
            policy.run(mock_fn)
        assert exc_info.value.retryable is False
        assert mock_fn.call_count == 1

    def test_retry_policy_backoff_timing(self):
        """RetryPolicy applies exponential backoff delays."""
        import time
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.1, backoff_factor=2.0)
        mock_fn = Mock(side_effect=[
            ProviderError("rate limit", "nvidia", retryable=True),
            ProviderError("rate limit", "nvidia", retryable=True),
            "success"
        ])
        start = time.time()
        policy.run(mock_fn)
        elapsed = time.time() - start
        # Should have slept: 0.1 * 2^0 + 0.1 * 2^1 = 0.1 + 0.2 = 0.3s
        assert elapsed >= 0.25  # Allow some margin


class TestProviderRuntimeExecutionPolicy429:
    """Test ProviderRuntimeExecutionPolicy behavior with 429 errors."""

    def test_execution_policy_default_retry(self):
        """ProviderRuntimeExecutionPolicy has default retry policy."""
        policy = ProviderRuntimeExecutionPolicy()
        assert policy.retry_policy.max_attempts == 3

    def test_execution_policy_retry_on_429(self):
        """ProviderRuntimeExecutionPolicy retries on 429 error."""
        policy = ProviderRuntimeExecutionPolicy(
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        )
        mock_provider = Mock()
        mock_provider.name = "nvidia"
        mock_provider.complete.side_effect = [
            ProviderError("NVIDIA API error 429: Too Many Requests", "nvidia", retryable=True),
            ProviderResponse(text="success", provider="nvidia", model="test", metadata={})
        ]
        request = ProviderRequest(prompt="test", model="test")
        result = policy.execute(mock_provider, request)
        assert result.response.text == "success"
        assert mock_provider.complete.call_count == 2

    def test_execution_policy_no_retry_on_non_retryable(self):
        """ProviderRuntimeExecutionPolicy does not retry on non-retryable error."""
        policy = ProviderRuntimeExecutionPolicy(
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
        )
        mock_provider = Mock()
        mock_provider.name = "nvidia"
        mock_provider.complete.side_effect = ProviderError("invalid api key", "nvidia", retryable=False)
        request = ProviderRequest(prompt="test", model="test")
        with pytest.raises(ProviderError) as exc_info:
            policy.execute(mock_provider, request)
        assert exc_info.value.retryable is False
        assert mock_provider.complete.call_count == 1

    def test_execution_policy_rate_limiter_blocks(self):
        """ProviderRuntimeExecutionPolicy respects rate limiter."""
        from core.ai_provider.rate_limiter import RateLimiter
        policy = ProviderRuntimeExecutionPolicy(
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.0),
            rate_limiter=RateLimiter(max_calls=0)  # No calls allowed
        )
        mock_provider = Mock()
        mock_provider.name = "nvidia"
        request = ProviderRequest(prompt="test", model="test")
        with pytest.raises(ProviderError) as exc_info:
            policy.execute(mock_provider, request)
        assert exc_info.value.status_code == 429
        assert "rate limit exceeded" in str(exc_info.value).lower()


class TestAdaptiveRetryPolicy429:
    """Test AdaptiveRetryPolicy decisions for 429."""

    def test_adaptive_policy_429_retryable(self):
        """AdaptiveRetryPolicy decides retry for http_429."""
        policy = AdaptiveRetryPolicy()
        # attempt=1 -> next_attempt=2 -> delay = base * 2^(2-1) = 5 * 2 = 10
        decision = policy.decide({"outcome": "http_429", "attempt": 1}, {"max_attempts": 3, "base_delay_seconds": 5, "max_delay_seconds": 60})
        assert decision["retry"] is True
        assert decision["delay_seconds"] == 10

    def test_adaptive_policy_429_backoff_increases(self):
        """AdaptiveRetryPolicy increases backoff for subsequent 429 retries."""
        policy = AdaptiveRetryPolicy()
        # attempt=1 -> next=2 -> 5*2=10
        decision1 = policy.decide({"outcome": "http_429", "attempt": 1}, {"max_attempts": 5, "base_delay_seconds": 5, "max_delay_seconds": 60})
        # attempt=2 -> next=3 -> 5*4=20
        decision2 = policy.decide({"outcome": "http_429", "attempt": 2}, {"max_attempts": 5, "base_delay_seconds": 5, "max_delay_seconds": 60})
        # attempt=3 -> next=4 -> 5*8=40
        decision3 = policy.decide({"outcome": "http_429", "attempt": 3}, {"max_attempts": 5, "base_delay_seconds": 5, "max_delay_seconds": 60})
        assert decision1["delay_seconds"] == 10
        assert decision2["delay_seconds"] == 20
        assert decision3["delay_seconds"] == 40

    def test_adaptive_policy_429_max_attempts_stops(self):
        """AdaptiveRetryPolicy stops retry after max attempts."""
        policy = AdaptiveRetryPolicy()
        decision = policy.decide({"outcome": "http_429", "attempt": 3}, {"max_attempts": 3, "base_delay_seconds": 5})
        assert decision["retry"] is False
        assert decision["stop"] is True
        assert decision["reason"] == "max_attempts_reached"

    def test_adaptive_policy_429_provider_switch_after_attempt(self):
        """AdaptiveRetryPolicy suggests provider switch after configured attempts."""
        policy = AdaptiveRetryPolicy()
        decision = policy.decide(
            {"outcome": "http_429", "attempt": 2},
            {"max_attempts": 5, "base_delay_seconds": 5, "allow_provider_switch": True, "provider_switch_after_attempt": 2}
        )
        assert decision["switch_provider"] is True

    def test_adaptive_policy_success_no_retry(self):
        """AdaptiveRetryPolicy does not retry on success."""
        policy = AdaptiveRetryPolicy()
        decision = policy.decide({"outcome": "success", "attempt": 1}, {"max_attempts": 3})
        assert decision["retry"] is False
        assert decision["stop"] is True
        assert decision["reason"] == "already_successful"


class TestTranslationProviderSettings:
    """Test TranslationProviderSettings loads retry config correctly."""

    def test_settings_load_retry_defaults(self, tmp_path):
        """TranslationProviderSettings loads retry defaults from config."""
        config_path = tmp_path / "config" / "provider_config.json"
        config_path.parent.mkdir(parents=True)
        import json
        config_path.write_text(json.dumps({
            "translation_engine_v3": {
                "retry_defaults": {
                    "max_attempts": 3,
                    "base_delay_seconds": 5.0,
                    "backoff_factor": 2.0
                }
            }
        }))

        settings = TranslationProviderSettings.load(tmp_path)
        assert settings.retry_attempts == 3
        assert settings.retry_base_delay_seconds == 5.0
        assert settings.retry_backoff_factor == 2.0

    def test_settings_fallback_to_defaults(self, tmp_path):
        """TranslationProviderSettings falls back to defaults when config missing."""
        config_path = tmp_path / "config" / "provider_config.json"
        config_path.parent.mkdir(parents=True)
        import json
        config_path.write_text(json.dumps({}))

        settings = TranslationProviderSettings.load(tmp_path)
        assert settings.retry_attempts == 1
        assert settings.retry_base_delay_seconds == 0.0
        assert settings.retry_backoff_factor == 2.0


class TestBuildTranslationProviderManagerRetry:
    """Test build_translation_provider_manager respects retry overrides."""

    def test_build_provider_manager_uses_settings_defaults(self, tmp_path):
        """build_translation_provider_manager uses settings defaults."""
        config_path = tmp_path / "config" / "provider_config.json"
        config_path.parent.mkdir(parents=True)
        import json
        config_path.write_text(json.dumps({
            "translation_engine_v3": {
                "retry_defaults": {
                    "max_attempts": 3,
                    "base_delay_seconds": 5.0,
                    "backoff_factor": 2.0
                },
                "fallback_models": []
            }
        }))

        manager = build_translation_provider_manager(
            root=tmp_path,
            api_key="test-key",
            primary_model="test-model",
            api_url="https://test.api",
            timeout=60,
            rpm_limit=40,
        )
        assert manager.retry_policy.max_attempts == 3
        assert manager.retry_policy.base_delay_seconds == 5.0
        assert manager.retry_policy.backoff_factor == 2.0

    def test_build_provider_manager_override_max_attempts(self, tmp_path):
        """build_translation_provider_manager accepts max_attempts override."""
        config_path = tmp_path / "config" / "provider_config.json"
        config_path.parent.mkdir(parents=True)
        import json
        config_path.write_text(json.dumps({
            "translation_engine_v3": {
                "retry_defaults": {
                    "max_attempts": 1,
                    "base_delay_seconds": 0.0,
                    "backoff_factor": 2.0
                },
                "fallback_models": []
            }
        }))

        manager = build_translation_provider_manager(
            root=tmp_path,
            api_key="test-key",
            primary_model="test-model",
            api_url="https://test.api",
            timeout=60,
            rpm_limit=40,
            max_attempts=5,
            retry_base_delay_seconds=10.0,
        )
        assert manager.retry_policy.max_attempts == 5
        assert manager.retry_policy.base_delay_seconds == 10.0


class Test429Classification:
    """Test 429 classification across different modules."""

    def test_retryable_patterns_include_429(self):
        """RETRYABLE_PROVIDER_ERROR_PATTERNS includes 429 variants."""
        from core.translation_engine.provider_runtime import RETRYABLE_PROVIDER_ERROR_PATTERNS
        patterns = [p.lower() for p in RETRYABLE_PROVIDER_ERROR_PATTERNS]
        assert "429" in patterns
        assert "rate limit" in patterns
        assert "too many requests" in patterns

    def test_is_retryable_translation_provider_error_429(self):
        """is_retryable_translation_provider_error returns True for 429."""
        from core.translation_engine.provider_runtime import is_retryable_translation_provider_error
        assert is_retryable_translation_provider_error("NVIDIA API error 429: Too Many Requests") is True
        assert is_retryable_translation_provider_error("rate limit exceeded") is True
        assert is_retryable_translation_provider_error("too many requests") is True

    def test_is_retryable_translation_provider_error_non_retryable(self):
        """is_retryable_translation_provider_error returns False for auth errors."""
        from core.translation_engine.provider_runtime import is_retryable_translation_provider_error
        assert is_retryable_translation_provider_error("401 Unauthorized") is False
        assert is_retryable_translation_provider_error("403 Forbidden") is False
        assert is_retryable_translation_provider_error("invalid api key") is False

    def test_controlled_routing_classification_429(self):
        """Controlled provider routing classifies rate_limit as retryable."""
        from core.controlled_provider_routing.classification import _RETRYABLE, _FALLBACK, classify_provider_failure
        assert "rate_limit" in _RETRYABLE
        assert "rate_limit" in _FALLBACK
        result = classify_provider_failure("rate_limit")
        assert result["retryable"] is True
        assert result["fallback_eligible"] is True
        assert result["cooldown_seconds"] == 60


class TestRuntimePipelineRetryIntegration:
    """Integration tests for runtime pipeline retry configuration."""

    def test_translate_package_from_request_passes_provider_attempts(self):
        """translate_package_from_request passes provider_attempts to provider manager."""
        from core.translation_engine.translation_engine import TranslationEngine
        from core.translation_runtime.models import TranslationRequest

        engine = TranslationEngine(root="/tmp", api_key="test")
        request = TranslationRequest(
            prompt="test prompt",
            metadata={
                "model_profile": {"model": "test-model"},
                "system_prompt": "system",
                "provider_attempts": 5,
                "retry_base_seconds": 10.0,
            },
            runtime_snapshot={},
            snapshot_id="test",
            prompt_hash="abc123",
            section_count=1,
            token_count=100,
        )

        with patch.object(engine, '_get_api_url_from_request', return_value="https://test.api"):
            with patch.object(engine, '_get_timeout_from_request', return_value=60):
                with patch.object(engine, '_get_rpm_limit_from_request', return_value=40):
                    with patch('core.translation_engine.translation_engine.build_translation_provider_manager') as mock_build:
                        mock_manager = Mock()
                        mock_manager.complete.return_value = ProviderResponse(
                            text="success", provider="nvidia", model="test", metadata={}
                        )
                        mock_build.return_value = mock_manager

                        result = engine.translate_package_from_request(request)

                        # Verify build_translation_provider_manager was called with override params
                        mock_build.assert_called_once()
                        call_kwargs = mock_build.call_args.kwargs
                        assert call_kwargs.get("max_attempts") == 5
                        assert call_kwargs.get("retry_base_delay_seconds") == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])