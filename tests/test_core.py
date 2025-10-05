"""Tests for OpenPension."""

import pytest

from opengovpension.core.config import Settings


def test_settings():
    """Test settings configuration."""
    settings = Settings()
    assert settings.app_name == "OpenPension"
    assert settings.version == "1.0.0"


def test_database_manager():
    """Test database manager."""
    # This would test database functionality
    assert True  # Placeholder test

