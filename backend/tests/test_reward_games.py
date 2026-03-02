"""Tests for reward game config and admin routes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.game_config import (
    ALL_GAMES,
    GAME_META,
    get_all_games_status,
    get_enabled_games,
    toggle_game,
    _CONFIG_PATH,
    _load,
    _save,
)


@pytest.fixture(autouse=True)
def _temp_config(tmp_path):
    """Redirect game config to a temp file for each test."""
    cfg_path = tmp_path / "game_config.json"
    with patch("app.services.game_config._CONFIG_PATH", cfg_path):
        yield cfg_path


class TestGameConfig:
    """Tests for game_config service."""

    def test_all_games_listed(self):
        """ALL_GAMES has 10 entries."""
        assert len(ALL_GAMES) == 10

    def test_all_games_have_meta(self):
        """Every game in ALL_GAMES has metadata."""
        for g in ALL_GAMES:
            assert g in GAME_META, f"Missing meta for {g}"
            assert "name" in GAME_META[g]
            assert "icon" in GAME_META[g]

    def test_default_all_enabled(self):
        """With no config file, all games are enabled."""
        enabled = get_enabled_games()
        assert set(enabled) == set(ALL_GAMES)

    def test_toggle_disables_game(self, _temp_config):
        """Toggling a game off removes it from enabled list."""
        assert toggle_game("sudoku", False)
        enabled = get_enabled_games()
        assert "sudoku" not in enabled
        assert len(enabled) == len(ALL_GAMES) - 1

    def test_toggle_enables_game(self, _temp_config):
        """Toggling a game on adds it back."""
        toggle_game("sudoku", False)
        toggle_game("sudoku", True)
        enabled = get_enabled_games()
        assert "sudoku" in enabled

    def test_toggle_unknown_game(self):
        """Toggling an unknown game ID returns False."""
        assert not toggle_game("nonexistent_game", True)

    def test_get_all_games_status(self, _temp_config):
        """get_all_games_status returns all games with correct structure."""
        toggle_game("tictactoe", False)
        status = get_all_games_status()
        assert len(status) == 10
        ttt = next(g for g in status if g["id"] == "tictactoe")
        assert ttt["enabled"] is False
        assert ttt["name"] == "Tic-Tac-Toe"
        assert ttt["icon"] == "⭕"
        sdk = next(g for g in status if g["id"] == "sudoku")
        assert sdk["enabled"] is True

    def test_config_persists(self, _temp_config):
        """Config changes persist across load calls."""
        toggle_game("space_invaders", False)
        toggle_game("mini_2048", False)
        # Simulate fresh load
        enabled = get_enabled_games()
        assert "space_invaders" not in enabled
        assert "mini_2048" not in enabled
        assert "sudoku" in enabled

    def test_multiple_toggles(self, _temp_config):
        """Multiple toggles work correctly."""
        for g in ALL_GAMES[:5]:
            toggle_game(g, False)
        enabled = get_enabled_games()
        assert len(enabled) == 5
        assert set(enabled) == set(ALL_GAMES[5:])

    def test_config_file_created(self, _temp_config):
        """Config file is created on first toggle."""
        assert not _temp_config.exists()
        toggle_game("sudoku", False)
        assert _temp_config.exists()
        data = json.loads(_temp_config.read_text())
        assert "enabled" in data
        assert data["enabled"]["sudoku"] is False


class TestMilestoneGameIntegration:
    """Test that milestone triggers use enabled games."""

    def test_enabled_games_returns_list(self):
        """get_enabled_games returns a list of strings."""
        result = get_enabled_games()
        assert isinstance(result, list)
        assert all(isinstance(g, str) for g in result)

    def test_enabled_games_subset_of_all(self, _temp_config):
        """Enabled games are always a subset of ALL_GAMES."""
        toggle_game("reflex_tap", False)
        enabled = get_enabled_games()
        assert set(enabled).issubset(set(ALL_GAMES))
