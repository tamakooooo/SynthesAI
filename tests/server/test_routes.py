"""
Tests for server routes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


class TestSystemRoutes:
    """Tests for system routes (health, readiness, feishu)."""

    def test_health_check(self) -> None:
        """Test health check endpoint."""
        from learning_assistant.server.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_check_not_initialized(self) -> None:
        """Test readiness when ServerContext not initialized."""
        from learning_assistant.server.main import app
        from learning_assistant.server.context import ServerContext

        # Mock not initialized
        with patch.object(ServerContext, 'is_initialized', return_value=False):
            client = TestClient(app)
            response = client.get("/ready")

            assert response.status_code == 200
            assert response.json()["status"] == "not_ready"


class TestFeishuRoutes:
    """Tests for Feishu-related system routes."""

    def test_check_feishu_configuration_disabled(self) -> None:
        """Test feishu check when adapter is disabled."""
        from learning_assistant.server.main import app
        from learning_assistant.server.context import ServerContext
        from learning_assistant.core.config_manager import ConfigManager, Adapters, Settings, Modules

        # Mock ServerContext
        mock_config_manager = Mock(spec=ConfigManager)
        mock_adapters = Mock(spec=Adapters)
        mock_adapters.feishu = Mock()
        mock_adapters.feishu.model_dump.return_value = {
            "enabled": False,
            "config": {}
        }
        mock_config_manager.adapters_model = mock_adapters

        mock_plugin_manager = Mock()
        mock_plugin_manager.get_plugin.return_value = None

        with patch.object(ServerContext, 'is_initialized', return_value=True), \
             patch.object(ServerContext, 'get_config_manager', return_value=mock_config_manager), \
             patch.object(ServerContext, 'plugin_manager', mock_plugin_manager):
            client = TestClient(app)
            response = client.get("/system/feishu/check")

            assert response.status_code == 200
            assert response.json()["enabled"] is False

    def test_publish_test_document_adapter_not_loaded(self) -> None:
        """Test publish-test when adapter not loaded."""
        from learning_assistant.server.main import app
        from learning_assistant.server.context import ServerContext

        mock_plugin_manager = Mock()
        mock_plugin_manager.get_plugin.return_value = None

        with patch.object(ServerContext, 'is_initialized', return_value=True), \
             patch.object(ServerContext, 'plugin_manager', mock_plugin_manager):
            client = TestClient(app)
            response = client.post("/system/feishu/publish-test")

            assert response.status_code == 404


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_get_all_auth_status(self) -> None:
        """Test getting auth status for all platforms."""
        from learning_assistant.server.main import app

        client = TestClient(app)
        response = client.get("/api/v1/auth/status")

        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        assert len(data["platforms"]) >= 3  # bilibili, douyin, youtube

    def test_get_platform_auth_status_bilibili(self) -> None:
        """Test getting auth status for bilibili."""
        from learning_assistant.server.main import app
        from learning_assistant.auth.providers import BilibiliAuthProvider
        from learning_assistant.auth.models import AuthInfo, AuthStatus

        # Mock provider
        mock_result = AuthInfo(
            platform="bilibili",
            status=AuthStatus.NOT_AUTHENTICATED,
        )

        with patch('learning_assistant.server.routes.auth.get_bilibili_provider') as mock_provider:
            provider = Mock(spec=BilibiliAuthProvider)
            provider.check_status.return_value = mock_result
            mock_provider.return_value = provider

            client = TestClient(app)
            response = client.get("/api/v1/auth/status/bilibili")

            assert response.status_code == 200
            assert response.json()["platform"] == "bilibili"

    def test_logout_platform(self) -> None:
        """Test logout endpoint."""
        from learning_assistant.server.main import app

        client = TestClient(app)
        response = client.delete("/api/v1/auth/bilibili")

        assert response.status_code == 200
        assert response.json()["success"] is True


class TestConfigurationRoutes:
    """Tests for configuration routes."""

    def test_get_configuration_endpoint_exists(self) -> None:
        """Test configuration endpoint exists."""
        from learning_assistant.server.main import app

        # Just verify the route exists - the endpoint requires ServerContext
        # which needs full initialization, so we skip the full integration test
        routes = [route.path for route in app.routes]
        assert "/api/v1/configuration" in routes