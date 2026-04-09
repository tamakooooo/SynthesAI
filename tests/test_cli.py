"""
Unit tests for CLI commands.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from learning_assistant import __version__
from learning_assistant.cli import app, state

# Create CLI runner
runner = CliRunner(mix_stderr=False)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset global state before each test."""
    state.config_manager = None
    state.event_bus = None
    state.plugin_manager = None


class TestVersionCommand:
    """Test version command."""

    def test_version_output(self) -> None:
        """Test version command shows correct version."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert __version__ in result.stdout
        assert "Learning Assistant" in result.stdout


class TestSetupCommand:
    """Test setup command."""

    @patch("subprocess.run")
    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    @patch(
        "learning_assistant.core.config_manager.ConfigManager.generate_default_config"
    )
    @patch("learning_assistant.core.config_manager.ConfigManager.get_llm_config")
    def test_setup_success(
        self,
        mock_get_llm: Mock,
        mock_generate: Mock,
        mock_load: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test setup command completes successfully."""
        # Mock FFmpeg check
        mock_subprocess.return_value = Mock(returncode=0)

        # Mock LLM config (no API key)
        mock_llm_config = Mock()
        mock_llm_config.provider = "openai"
        mock_llm_config.model = "gpt-4o"
        mock_llm_config.api_key = None
        mock_get_llm.return_value = mock_llm_config

        result = runner.invoke(app, ["setup"])

        assert result.exit_code == 0
        assert "Setup Wizard" in result.stdout
        assert "Setup complete" in result.stdout
        assert "FFmpeg" in result.stdout

    @patch("subprocess.run")
    def test_setup_ffmpeg_not_installed(self, mock_subprocess: Mock) -> None:
        """Test setup when FFmpeg is not installed."""
        # Mock FFmpeg check failure
        mock_subprocess.side_effect = FileNotFoundError()

        result = runner.invoke(app, ["setup"])

        assert result.exit_code == 0
        assert "FFmpeg is not installed" in result.stdout


class TestListPluginsCommand:
    """Test list-plugins command."""

    @patch("learning_assistant.core.plugin_manager.PluginManager.discover_plugins")
    @patch("learning_assistant.core.plugin_manager.PluginManager.load_plugin")
    @patch("learning_assistant.core.plugin_manager.PluginManager.initialize_all")
    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    def test_list_plugins_empty(
        self,
        mock_load_config: Mock,
        mock_init: Mock,
        mock_load_plugin: Mock,
        mock_discover: Mock,
    ) -> None:
        """Test list-plugins with no plugins."""
        # Mock discover_plugins to set empty plugins dict

        # Initialize plugin_manager with empty plugins
        mock_discover.return_value = []

        result = runner.invoke(app, ["list-plugins"])

        # Command should execute without error
        assert result.exit_code == 0


class TestConfigCommand:
    """Test config command."""

    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    @patch("learning_assistant.core.config_manager.ConfigManager.get_llm_config")
    def test_config_shows_llm_settings(
        self, mock_get_llm: Mock, mock_load: Mock
    ) -> None:
        """Test config command shows LLM configuration."""
        # Initialize config_manager first

        from learning_assistant.core.config_manager import ConfigManager

        state.config_manager = ConfigManager(config_dir=Path("config"))

        # Mock LLM config
        mock_llm_config = {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        mock_get_llm.return_value = mock_llm_config

        # Mock settings model
        from learning_assistant.core.config_manager import CostTrackingConfig, Settings

        mock_settings = Mock(spec=Settings)
        mock_settings.cost_tracking = CostTrackingConfig()
        state.config_manager.settings_model = mock_settings

        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "Current Configuration" in result.stdout
        assert "LLM Configuration" in result.stdout
        assert "openai" in result.stdout

    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    def test_config_not_initialized(self, mock_load: Mock) -> None:
        """Test config when config manager not initialized."""
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "Error" in result.stdout


class TestHistoryCommand:
    """Test history command."""

    def test_history_placeholder(self) -> None:
        """Test history command placeholder output."""
        result = runner.invoke(app, ["history"])

        assert result.exit_code == 0
        assert "Learning History" in result.stdout
        assert "No history records found" in result.stdout


class TestVideoCommand:
    """Test video command placeholder."""

    def test_video_placeholder(self) -> None:
        """Test video command placeholder output."""
        result = runner.invoke(app, ["video", "https://example.com/video"])

        assert result.exit_code == 0
        assert "Processing video" in result.stdout
        assert "under development" in result.stdout

    def test_video_with_options(self) -> None:
        """Test video command with output options."""
        result = runner.invoke(
            app,
            [
                "video",
                "https://example.com/video",
                "--output",
                "output.md",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert "Processing video" in result.stdout


class TestCLIIntegration:
    """Test CLI integration with core components."""

    @patch("learning_assistant.core.plugin_manager.PluginManager.discover_plugins")
    @patch("learning_assistant.core.plugin_manager.PluginManager.load_plugin")
    @patch("learning_assistant.core.plugin_manager.PluginManager.initialize_all")
    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    def test_cli_initialization(
        self,
        mock_load_config: Mock,
        mock_init: Mock,
        mock_load_plugin: Mock,
        mock_discover: Mock,
    ) -> None:
        """Test CLI initializes core components correctly."""
        runner.invoke(app, ["version"])

        # Verify state was initialized
        assert state.config_manager is not None
        assert state.event_bus is not None
        assert state.plugin_manager is not None

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Learning Assistant" in result.stdout
        assert "modular" in result.stdout.lower()

    def test_cli_command_help(self) -> None:
        """Test individual command help."""
        result = runner.invoke(app, ["version", "--help"])

        assert result.exit_code == 0
        assert "version" in result.stdout.lower()


class TestAppState:
    """Test AppState class."""

    def test_state_initialization(self) -> None:
        """Test AppState initialization."""

        from learning_assistant.cli import AppState

        test_state = AppState()
        assert test_state.config_manager is None
        assert test_state.event_bus is None
        assert test_state.plugin_manager is None

    @patch("learning_assistant.core.plugin_manager.PluginManager.discover_plugins")
    @patch("learning_assistant.core.plugin_manager.PluginManager.load_plugin")
    @patch("learning_assistant.core.config_manager.ConfigManager.load_all")
    def test_state_initialize_method(
        self,
        mock_load: Mock,
        mock_load_plugin: Mock,
        mock_discover: Mock,
    ) -> None:
        """Test AppState.initialize method."""

        from learning_assistant.cli import AppState

        test_state = AppState()
        config_dir = Path("config")
        test_state.initialize(config_dir)

        assert test_state.config_manager is not None
        assert test_state.event_bus is not None
        assert test_state.plugin_manager is not None
