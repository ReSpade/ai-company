"""Tests for configuration and settings."""

from pathlib import Path

from ai_company.config.settings import Settings


def test_default_settings():
    settings = Settings()
    assert settings.default_model == "sonnet"
    assert settings.reviewer_model == "opus"
    assert settings.max_turns == 30
    assert settings.log_level == "INFO"


def test_projects_dir():
    settings = Settings()
    assert isinstance(settings.projects_dir, Path)


def test_data_dir():
    settings = Settings()
    assert isinstance(settings.data_dir, Path)
