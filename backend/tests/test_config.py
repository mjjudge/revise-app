"""Tests for the config module."""

import os


def test_settings_defaults():
    """Settings loads with sensible defaults."""
    from app.core.config import Settings

    s = Settings(database_url="sqlite:///test.db")
    assert s.app_env == "dev"
    assert s.child_name == "Anna"
    assert "Chibs" in s.nickname_list
    assert "Chibby" in s.nickname_list
    assert s.session_max_age == 86400


def test_settings_sqlite_path():
    """sqlite_path extracts the file path from the URL."""
    from app.core.config import Settings

    s = Settings(database_url="sqlite:////data/app.sqlite3")
    assert str(s.sqlite_path) == "/data/app.sqlite3"
