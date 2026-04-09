"""
Unit tests for LLM Service and Providers.
"""

from unittest.mock import Mock, patch

import pytest

from learning_assistant.core.llm.providers.anthropic import AnthropicProvider
from learning_assistant.core.llm.providers.deepseek import DeepSeekProvider
from learning_assistant.core.llm.providers.openai import OpenAIProvider
from learning_assistant.core.llm.service import LLMService


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    def test_init(self) -> None:
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

        assert provider.model == "gpt-4o"
        assert provider.client is not None

    def test_get_available_models(self) -> None:
        """Test getting available models."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        models = provider.get_available_models()

        assert "gpt-4o" in models
        assert "gpt-4-turbo" in models
        assert "gpt-3.5-turbo" in models

    def test_estimate_cost(self) -> None:
        """Test cost estimation."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.estimate_cost(usage)

        # Expected: (1000 * 0.005 / 1000) + (500 * 0.015 / 1000) = 0.005 + 0.0075 = 0.0125
        assert cost == 0.0125

    def test_estimate_cost_unknown_model(self) -> None:
        """Test cost estimation for unknown model."""
        provider = OpenAIProvider(api_key="test-key", model="unknown-model")

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.estimate_cost(usage)

        assert cost == 0.0

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_call(self, mock_openai_class: Mock) -> None:
        """Test calling OpenAI API."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(content="Test response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Call provider
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        response = provider.call("Test prompt", temperature=0.7, max_tokens=100)

        # Verify response
        assert response.content == "Test response"
        assert response.model == "gpt-4o"
        assert response.usage["prompt_tokens"] == 100
        assert response.usage["completion_tokens"] == 50
        assert response.usage["total_tokens"] == 150
        assert response.metadata["finish_reason"] == "stop"

        # Verify API call
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=100,
        )

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_validate_api_key_success(self, mock_openai_class: Mock) -> None:
        """Test API key validation success."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Validate key
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        result = provider.validate_api_key()

        assert result is True

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_validate_api_key_failure(self, mock_openai_class: Mock) -> None:
        """Test API key validation failure."""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        mock_openai_class.return_value = mock_client

        # Validate key
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        result = provider.validate_api_key()

        assert result is False


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    def test_init(self) -> None:
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )

        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.client is not None

    def test_get_available_models(self) -> None:
        """Test getting available models."""
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )
        models = provider.get_available_models()

        assert "claude-3-5-sonnet-20241022" in models
        assert "claude-3-opus-20240229" in models
        assert "claude-3-haiku-20240307" in models

    def test_estimate_cost(self) -> None:
        """Test cost estimation."""
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.estimate_cost(usage)

        # Expected: (1000 * 0.003 / 1000) + (500 * 0.015 / 1000) = 0.003 + 0.0075 = 0.0105
        # Use pytest.approx for floating-point comparison
        assert cost == pytest.approx(0.0105)

    @patch("learning_assistant.core.llm.providers.anthropic.Anthropic")
    def test_call(self, mock_anthropic_class: Mock) -> None:
        """Test calling Anthropic API."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Call provider
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )
        response = provider.call("Test prompt", temperature=0.7, max_tokens=100)

        # Verify response
        assert response.content == "Test response"
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.usage["prompt_tokens"] == 100
        assert response.usage["completion_tokens"] == 50
        assert response.usage["total_tokens"] == 150
        assert response.metadata["stop_reason"] == "end_turn"

        # Verify API call
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
        )

    @patch("learning_assistant.core.llm.providers.anthropic.Anthropic")
    def test_validate_api_key_success(self, mock_anthropic_class: Mock) -> None:
        """Test API key validation success."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Validate key
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )
        result = provider.validate_api_key()

        assert result is True

    @patch("learning_assistant.core.llm.providers.anthropic.Anthropic")
    def test_validate_api_key_failure(self, mock_anthropic_class: Mock) -> None:
        """Test API key validation failure."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Invalid API key")
        mock_anthropic_class.return_value = mock_client

        # Validate key
        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-sonnet-20241022"
        )
        result = provider.validate_api_key()

        assert result is False


class TestDeepSeekProvider:
    """Test DeepSeek provider implementation."""

    def test_init(self) -> None:
        """Test DeepSeek provider initialization."""
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")

        assert provider.model == "deepseek-chat"
        assert provider.client is not None
        # OpenAI SDK automatically handles base_url (does not need /v1 suffix)
        assert str(provider.client.base_url) == "https://api.deepseek.com"

    def test_get_available_models(self) -> None:
        """Test getting available models."""
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")
        models = provider.get_available_models()

        assert "deepseek-chat" in models
        assert "deepseek-coder" in models

    def test_estimate_cost(self) -> None:
        """Test cost estimation."""
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.estimate_cost(usage)

        # Expected: (1000 * 0.001 / 1000) + (500 * 0.002 / 1000) = 0.001 + 0.001 = 0.002
        assert cost == 0.002

    @patch("learning_assistant.core.llm.providers.deepseek.OpenAI")
    def test_call(self, mock_openai_class: Mock) -> None:
        """Test calling DeepSeek API."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(content="Test response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Call provider
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")
        response = provider.call("Test prompt", temperature=0.7, max_tokens=100)

        # Verify response
        assert response.content == "Test response"
        assert response.model == "deepseek-chat"
        assert response.usage["prompt_tokens"] == 100
        assert response.usage["completion_tokens"] == 50
        assert response.usage["total_tokens"] == 150

        # Verify API call
        mock_client.chat.completions.create.assert_called_once_with(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=100,
        )

    @patch("learning_assistant.core.llm.providers.deepseek.OpenAI")
    def test_validate_api_key_success(self, mock_openai_class: Mock) -> None:
        """Test API key validation success."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Validate key
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")
        result = provider.validate_api_key()

        assert result is True

    @patch("learning_assistant.core.llm.providers.deepseek.OpenAI")
    def test_validate_api_key_failure(self, mock_openai_class: Mock) -> None:
        """Test API key validation failure."""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        mock_openai_class.return_value = mock_client

        # Validate key
        provider = DeepSeekProvider(api_key="test-key", model="deepseek-chat")
        result = provider.validate_api_key()

        assert result is False


class TestLLMService:
    """Test LLM Service."""

    def test_init_openai(self) -> None:
        """Test LLMService initialization with OpenAI provider."""
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")

        assert service.provider_name == "openai"
        assert service.model == "gpt-4o"
        assert service.provider is not None

    def test_init_anthropic(self) -> None:
        """Test LLMService initialization with Anthropic provider."""
        service = LLMService(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
        )

        assert service.provider_name == "anthropic"
        assert service.model == "claude-3-5-sonnet-20241022"

    def test_init_deepseek(self) -> None:
        """Test LLMService initialization with DeepSeek provider."""
        service = LLMService(
            provider="deepseek", api_key="test-key", model="deepseek-chat"
        )

        assert service.provider_name == "deepseek"
        assert service.model == "deepseek-chat"

    def test_init_unsupported_provider(self) -> None:
        """Test LLMService initialization with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMService(provider="unsupported", api_key="test-key", model="test-model")

    def test_get_available_models(self) -> None:
        """Test getting available models."""
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")
        models = service.get_available_models()

        assert "gpt-4o" in models

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_call(self, mock_openai_class: Mock) -> None:
        """Test calling LLM through service."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"), finish_reason="stop")
        ]
        mock_response.usage = Mock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Call service
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")
        response = service.call("Test prompt")

        # Verify response
        assert response.content == "Test response"

        # Verify statistics updated
        assert service.call_count == 1
        assert service.total_tokens == 150
        assert service.total_cost > 0

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_call_with_retry_success(self, mock_openai_class: Mock) -> None:
        """Test retry mechanism with eventual success."""
        # Setup mock (fail twice, succeed on third attempt)
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"), finish_reason="stop")
        ]
        mock_response.usage = Mock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        # Fail twice, then succeed
        mock_client.chat.completions.create.side_effect = [
            Exception("API error 1"),
            Exception("API error 2"),
            mock_response,
        ]
        mock_openai_class.return_value = mock_client

        # Call service
        service = LLMService(
            provider="openai",
            api_key="test-key",
            model="gpt-4o",
            max_retries=3,
            retry_delay=0.1,
        )
        response = service.call("Test prompt")

        # Verify response
        assert response.content == "Test response"

        # Verify retry count
        assert service.retry_count == 2

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_call_with_retry_failure(self, mock_openai_class: Mock) -> None:
        """Test retry mechanism with failure after all retries."""
        # Setup mock (always fail)
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai_class.return_value = mock_client

        # Call service
        service = LLMService(
            provider="openai",
            api_key="test-key",
            model="gpt-4o",
            max_retries=3,
            retry_delay=0.1,
        )

        # Should raise exception after all retries
        with pytest.raises(Exception, match="API error"):
            service.call("Test prompt")

        # Verify retry count
        assert service.retry_count == 3

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_validate_api_key(self, mock_openai_class: Mock) -> None:
        """Test validating API key through service."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Validate key
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")
        result = service.validate_api_key()

        assert result is True

    def test_estimate_cost(self) -> None:
        """Test cost estimation through service."""
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = service.estimate_cost(usage)

        assert cost > 0

    @patch("learning_assistant.core.llm.providers.openai.OpenAI")
    def test_get_statistics(self, mock_openai_class: Mock) -> None:
        """Test getting statistics."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"), finish_reason="stop")
        ]
        mock_response.usage = Mock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Call service
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")
        service.call("Test prompt")

        # Get statistics
        stats = service.get_statistics()

        assert stats["provider"] == "openai"
        assert stats["model"] == "gpt-4o"
        assert stats["call_count"] == 1
        assert stats["total_tokens"] == 150
        assert stats["total_cost"] > 0
        assert stats["daily_cost"] > 0

    def test_reset_daily_cost(self) -> None:
        """Test resetting daily cost."""
        service = LLMService(provider="openai", api_key="test-key", model="gpt-4o")
        service.daily_cost = 10.0

        service.reset_daily_cost()

        assert service.daily_cost == 0.0
