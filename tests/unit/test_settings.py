"""Unit tests for application configuration settings."""

import os
from unittest import mock

from opsmind.settings.config import Settings


def test_default_settings() -> None:
    """Test default values of application settings."""
    settings = Settings()
    assert settings.app_name == "OpsMind"
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert "postgresql+psycopg://" in settings.database_url
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_custom_settings_override() -> None:
    """Test overriding settings with environment variables."""
    with mock.patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "staging",
            "DEBUG": "true",
            "APP_NAME": "OpsMind-Test",
            "APP_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
        },
    ):
        settings = Settings()
        assert settings.environment == "staging"
        assert settings.debug is True
        assert settings.app_name == "OpsMind-Test"
        assert settings.app_port == 9000
        assert settings.log_level == "DEBUG"
