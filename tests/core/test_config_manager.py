"""
Unit tests for ConfigManager.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from learning_assistant.core.config_manager import (
    AdapterConfig,
    Adapters,
    AppConfig,
    ConfigManager,
    CostTrackingConfig,
    LLMProviderConfig,
    ModuleConfig,
    Modules,
    Settings,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def valid_settings_dict() -> dict:
    """Valid settings configuration dict."""
    return {
        "app": {
            "name": "Test Assistant",
            "version": "1.0.0",
            "log_level": "DEBUG",
            "log_file": "logs/test.log",
        },
        "llm": {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "default_model": "gpt-4o",
                    "models": ["gpt-4o", "gpt-4-turbo"],
                    "timeout": 30,
                    "max_retries": 3,
                },
                "anthropic": {
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "default_model": "claude-3-5-sonnet-20241022",
                    "models": ["claude-3-5-sonnet-20241022"],
                    "timeout": 30,
                    "max_retries": 3,
                },
            },
            "cost_tracking": {
                "enabled": True,
                "daily_limit": 5.0,
                "monthly_limit": 50.0,
                "warning_threshold": 0.8,
            },
        },
        "cache": {
            "enabled": True,
            "directory": "data/cache",
            "expiry_days": 7,
            "max_size_mb": 500,
        },
        "history": {
            "enabled": True,
            "directory": "data/history",
            "max_records": 1000,
            "cleanup_days": 30,
        },
        "task": {
            "enabled": True,
            "directory": "data/tasks",
            "auto_resume": False,
            "max_concurrent": 3,
        },
        "output": {
            "default_format": "markdown",
            "directory": "data/outputs",
            "template_directory": "templates/outputs",
            "auto_subdirs": True,
        },
        "plugin": {
            "directories": ["src/learning_assistant/modules"],
            "hot_reload": False,
            "load_timeout": 5,
        },
        "performance": {
            "multiprocessing": True,
            "worker_count": 4,
            "memory_limit_mb": 500,
        },
        "security": {
            "validate_api_keys": True,
            "encrypt_storage": False,
            "allow_insecure": False,
        },
    }


@pytest.fixture
def valid_modules_dict() -> dict:
    """Valid modules configuration dict."""
    return {
        "modules": {
            "video_summary": {
                "enabled": True,
                "priority": 1,
                "config": {
                    "download": {
                        "output_dir": "data/cache/downloads",
                        "quality": "medium",
                    },
                },
            },
            "link_learning": {
                "enabled": False,
                "priority": 2,
                "config": {},
            },
        },
    }


@pytest.fixture
def valid_adapters_dict() -> dict:
    """Valid adapters configuration dict."""
    return {
        "adapters": {
            "feishu": {
                "enabled": False,
                "priority": 1,
                "config": {
                    "app_id_env": "FEISHU_APP_ID",
                },
            },
            "siyuan": {
                "enabled": False,
                "priority": 2,
                "config": {},
            },
        },
        "event_bus": {
            "enabled": True,
            "subscriptions": {
                "feishu": ["video.summarized"],
            },
            "retry": {
                "max_retries": 3,
                "delay": 5,
            },
        },
    }


class TestConfigManagerInit:
    """Test ConfigManager initialization."""

    def test_init_default_config_dir(self) -> None:
        """Test initialization with default config directory."""
        manager = ConfigManager()
        assert manager.config_dir == Path("config")
        assert manager.settings_model is None
        assert manager.modules_model is None
        assert manager.adapters_model is None

    def test_init_custom_config_dir(self, temp_config_dir: Path) -> None:
        """Test initialization with custom config directory."""
        manager = ConfigManager(config_dir=temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.settings_model is None
        assert manager.modules_model is None
        assert manager.adapters_model is None


class TestConfigManagerLoadAll:
    """Test ConfigManager.load_all() method."""

    def test_load_all_files_exist(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
        valid_modules_dict: dict,
        valid_adapters_dict: dict,
    ) -> None:
        """Test loading all configuration files when they exist."""
        # Write YAML files
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        modules_file = temp_config_dir / "modules.yaml"
        with modules_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_modules_dict, f)

        adapters_file = temp_config_dir / "adapters.yaml"
        with adapters_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_adapters_dict, f)

        # Load configurations
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        # Verify models are loaded
        assert manager.settings_model is not None
        assert manager.modules_model is not None
        assert manager.adapters_model is not None

        # Verify settings content
        assert manager.settings_model.app.name == "Test Assistant"
        assert manager.settings_model.llm.default_provider == "openai"

    def test_load_all_files_not_exist(self, temp_config_dir: Path) -> None:
        """Test loading when configuration files don't exist."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        # Should create default models
        assert manager.settings_model is not None
        assert manager.settings_model.app.name == "Learning Assistant"
        assert manager.modules_model is not None
        assert manager.adapters_model is not None

    def test_load_all_invalid_yaml(self, temp_config_dir: Path) -> None:
        """Test loading with invalid YAML file."""
        # Write invalid YAML
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        manager = ConfigManager(config_dir=temp_config_dir)
        with pytest.raises(yaml.YAMLError):
            manager.load_all()

    def test_load_all_invalid_config_structure(self, temp_config_dir: Path) -> None:
        """Test loading with invalid configuration structure."""
        # Write YAML with invalid structure (missing required field)
        invalid_settings = {
            "llm": {
                "default_provider": "unknown_provider",  # Provider not in providers dict
                "providers": {},
            },
        }

        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(invalid_settings, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        # Should load without validation error because validation happens at validate_config
        manager.load_all()


class TestConfigManagerGetLLMConfig:
    """Test ConfigManager.get_llm_config() method."""

    def test_get_llm_config_default_provider(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
    ) -> None:
        """Test getting default provider LLM config."""
        # Write settings.yaml
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            config = manager.get_llm_config()

        assert config["api_key"] == "test-api-key"
        assert config["default_model"] == "gpt-4o"
        assert config["timeout"] == 30
        assert "cost_tracking" in config

    def test_get_llm_config_specific_provider(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
    ) -> None:
        """Test getting specific provider LLM config."""
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"}):
            config = manager.get_llm_config("anthropic")

        assert config["api_key"] == "test-anthropic-key"
        assert config["default_model"] == "claude-3-5-sonnet-20241022"

    def test_get_llm_config_missing_api_key(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
    ) -> None:
        """Test getting LLM config when API key is missing."""
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        # Ensure API key env var is not set
        with patch.dict(os.environ, {}, clear=True):
            config = manager.get_llm_config("openai")

        assert config["api_key"] is None

    def test_get_llm_config_provider_not_found(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
    ) -> None:
        """Test getting LLM config for non-existent provider."""
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        with pytest.raises(ValueError, match="Provider 'unknown' not found"):
            manager.get_llm_config("unknown")

    def test_get_llm_config_settings_not_loaded(self) -> None:
        """Test getting LLM config before settings are loaded."""
        manager = ConfigManager()
        with pytest.raises(ValueError, match="Settings not loaded"):
            manager.get_llm_config()


class TestConfigManagerGetPluginConfig:
    """Test ConfigManager.get_plugin_config() method."""

    def test_get_module_config(
        self,
        temp_config_dir: Path,
        valid_modules_dict: dict,
    ) -> None:
        """Test getting module configuration."""
        modules_file = temp_config_dir / "modules.yaml"
        with modules_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_modules_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        config = manager.get_plugin_config("video_summary")

        assert config["enabled"] is True
        assert config["priority"] == 1
        assert "download" in config["config"]

    def test_get_adapter_config(
        self,
        temp_config_dir: Path,
        valid_adapters_dict: dict,
    ) -> None:
        """Test getting adapter configuration."""
        adapters_file = temp_config_dir / "adapters.yaml"
        with adapters_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_adapters_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        config = manager.get_plugin_config("feishu")

        assert config["enabled"] is False
        assert config["priority"] == 1
        assert "app_id_env" in config["config"]

    def test_get_plugin_config_not_found(
        self,
        temp_config_dir: Path,
        valid_modules_dict: dict,
        valid_adapters_dict: dict,
    ) -> None:
        """Test getting non-existent plugin configuration."""
        modules_file = temp_config_dir / "modules.yaml"
        with modules_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_modules_dict, f)

        adapters_file = temp_config_dir / "adapters.yaml"
        with adapters_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_adapters_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        with pytest.raises(ValueError, match="Plugin 'unknown_plugin' not found"):
            manager.get_plugin_config("unknown_plugin")


class TestConfigManagerGenerateDefaultConfig:
    """Test ConfigManager.generate_default_config() method."""

    def test_generate_default_config_creates_files(self, temp_config_dir: Path) -> None:
        """Test generating default configuration files."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.generate_default_config()

        # Check files are created
        assert (temp_config_dir / "settings.yaml").exists()
        assert (temp_config_dir / "modules.yaml").exists()
        assert (temp_config_dir / "adapters.yaml").exists()

    def test_generate_default_config_not_overwrite(self, temp_config_dir: Path) -> None:
        """Test that generate_default_config doesn't overwrite existing files."""
        # Create existing file with custom content
        settings_file = temp_config_dir / "settings.yaml"
        custom_content = {"app": {"name": "Custom Name"}}
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(custom_content, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.generate_default_config()

        # Load and verify content is unchanged
        with settings_file.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded["app"]["name"] == "Custom Name"

    def test_generate_default_config_creates_directory(self, tmp_path: Path) -> None:
        """Test that generate_default_config creates config directory if needed."""
        config_dir = tmp_path / "new_config"
        manager = ConfigManager(config_dir=config_dir)
        manager.generate_default_config()

        assert config_dir.exists()
        assert (config_dir / "settings.yaml").exists()


class TestConfigManagerValidateConfig:
    """Test ConfigManager.validate_config() method."""

    def test_validate_valid_config(self, valid_settings_dict: dict) -> None:
        """Test validating valid configuration."""
        manager = ConfigManager()
        validated = manager.validate_config(valid_settings_dict, Settings)

        assert isinstance(validated, Settings)
        assert validated.app.name == "Test Assistant"

    def test_validate_invalid_config_missing_required_field(self) -> None:
        """Test validating configuration with missing required field."""
        invalid_config = {
            "llm": {
                "providers": {
                    "openai": {
                        # Missing api_key_env (required field)
                        "default_model": "gpt-4o",
                    },
                },
            },
        }

        manager = ConfigManager()
        with pytest.raises(ValidationError):
            manager.validate_config(invalid_config, Settings)

    def test_validate_empty_config(self) -> None:
        """Test validating empty configuration."""
        manager = ConfigManager()
        validated = manager.validate_config({}, Settings)

        # Should use default values
        assert validated.app.name == "Learning Assistant"


class TestPydanticModels:
    """Test Pydantic validation models."""

    def test_app_config_defaults(self) -> None:
        """Test AppConfig default values."""
        config = AppConfig()
        assert config.name == "Learning Assistant"
        assert config.version == "0.1.0"
        assert config.log_level == "INFO"

    def test_llm_provider_config_required_fields(self) -> None:
        """Test LLMProviderConfig required fields."""
        # Valid config with all required fields
        config = LLMProviderConfig(
            api_key_env="OPENAI_API_KEY",
            default_model="gpt-4o",
        )
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.default_model == "gpt-4o"

        # Missing required field should raise ValidationError
        with pytest.raises(ValidationError):
            LLMProviderConfig(default_model="gpt-4o")  # Missing api_key_env

    def test_module_config_defaults(self) -> None:
        """Test ModuleConfig default values."""
        config = ModuleConfig()
        assert config.enabled is False
        assert config.priority == 99
        assert config.config == {}

    def test_adapter_config_defaults(self) -> None:
        """Test AdapterConfig default values."""
        config = AdapterConfig()
        assert config.enabled is False
        assert config.priority == 99
        assert config.config == {}

    def test_cost_tracking_config_defaults(self) -> None:
        """Test CostTrackingConfig default values."""
        config = CostTrackingConfig()
        assert config.enabled is True
        assert config.daily_limit == 10.0
        assert config.monthly_limit == 100.0

    def test_settings_model_nested_defaults(self) -> None:
        """Test Settings model nested default values."""
        settings = Settings()
        assert settings.app.name == "Learning Assistant"
        assert settings.llm.default_provider == "openai"
        assert settings.cache.enabled is True
        assert settings.history.enabled is True
        assert settings.task.enabled is True

    def test_modules_model_defaults(self) -> None:
        """Test Modules model default values."""
        modules = Modules()
        assert modules.video_summary.enabled is False
        assert modules.link_learning.enabled is False
        assert modules.vocabulary.enabled is False

    def test_adapters_model_defaults(self) -> None:
        """Test Adapters model default values."""
        adapters = Adapters()
        assert adapters.feishu.enabled is False
        assert adapters.siyuan.enabled is False
        assert adapters.obsidian.enabled is False
        assert adapters.event_bus.enabled is True


class TestConfigManagerHelperMethods:
    """Test ConfigManager helper methods."""

    def test_load_yaml_file_valid(
        self, temp_config_dir: Path, valid_settings_dict: dict
    ) -> None:
        """Test _load_yaml_file with valid YAML."""
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        loaded = manager._load_yaml_file(settings_file)

        assert loaded == valid_settings_dict

    def test_load_yaml_file_empty(self, temp_config_dir: Path) -> None:
        """Test _load_yaml_file with empty file."""
        empty_file = temp_config_dir / "empty.yaml"
        empty_file.touch()

        manager = ConfigManager(config_dir=temp_config_dir)
        loaded = manager._load_yaml_file(empty_file)

        assert loaded == {}

    def test_load_yaml_file_not_found(self, temp_config_dir: Path) -> None:
        """Test _load_yaml_file with non-existent file."""
        manager = ConfigManager(config_dir=temp_config_dir)
        missing_file = temp_config_dir / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            manager._load_yaml_file(missing_file)

    def test_write_yaml_file(
        self, temp_config_dir: Path, valid_settings_dict: dict
    ) -> None:
        """Test _write_yaml_file."""
        output_file = temp_config_dir / "output.yaml"

        manager = ConfigManager(config_dir=temp_config_dir)
        manager._write_yaml_file(output_file, valid_settings_dict)

        # Verify file exists and content matches
        assert output_file.exists()
        with output_file.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded == valid_settings_dict


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_full_workflow(
        self,
        temp_config_dir: Path,
        valid_settings_dict: dict,
        valid_modules_dict: dict,
        valid_adapters_dict: dict,
    ) -> None:
        """Test complete workflow: generate -> load -> retrieve."""
        # Step 1: Write configuration files
        settings_file = temp_config_dir / "settings.yaml"
        with settings_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_settings_dict, f)

        modules_file = temp_config_dir / "modules.yaml"
        with modules_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_modules_dict, f)

        adapters_file = temp_config_dir / "adapters.yaml"
        with adapters_file.open("w", encoding="utf-8") as f:
            yaml.dump(valid_adapters_dict, f)

        # Step 2: Load configurations
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load_all()

        # Step 3: Retrieve configurations
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            llm_config = manager.get_llm_config("openai")

        module_config = manager.get_plugin_config("video_summary")
        adapter_config = manager.get_plugin_config("feishu")

        # Verify all configs retrieved successfully
        assert llm_config["api_key"] == "test-key"
        assert module_config["enabled"] is True
        assert adapter_config["priority"] == 1

    def test_generate_and_load_defaults(self, temp_config_dir: Path) -> None:
        """Test generating default configs and loading them."""
        # Generate defaults
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.generate_default_config()

        # Load defaults
        manager.load_all()

        # Verify defaults loaded successfully
        assert manager.settings_model is not None
        assert manager.modules_model is not None
        assert manager.adapters_model is not None

        assert manager.settings_model.app.name == "Learning Assistant"
        assert manager.modules_model.video_summary.enabled is False
        assert manager.adapters_model.feishu.enabled is False
