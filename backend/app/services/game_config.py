"""Game configuration service — manages which reward mini-games are enabled."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Default config: all games enabled
ALL_GAMES = [
    "sudoku", "tictactoe", "space_invaders", "pattern_memory",
    "reflex_tap", "word_scramble", "mini_2048", "gravity_collector",
    "tangram", "pixel_art",
]

GAME_META = {
    "sudoku":           {"name": "Mini Sudoku",       "icon": "🧩"},
    "tictactoe":        {"name": "Tic-Tac-Toe",       "icon": "⭕"},
    "space_invaders":   {"name": "Space Invaders",     "icon": "🚀"},
    "pattern_memory":   {"name": "Pattern Memory",     "icon": "🧠"},
    "reflex_tap":       {"name": "Reflex Tap",         "icon": "⚡"},
    "word_scramble":    {"name": "Word Scramble",      "icon": "🔤"},
    "mini_2048":        {"name": "Mini 2048",          "icon": "🔢"},
    "gravity_collector":{"name": "Gravity Collector",  "icon": "🌌"},
    "tangram":          {"name": "Tangram Builder",    "icon": "🔷"},
    "pixel_art":        {"name": "Pixel Art Reveal",   "icon": "🎨"},
}

_CONFIG_PATH = Path(os.environ.get("DATA_DIR", "data")) / "game_config.json"


def _load() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text())
    return {"enabled": {g: True for g in ALL_GAMES}}


def _save(config: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_enabled_games() -> list[str]:
    """Return list of enabled game IDs."""
    config = _load()
    return [g for g in ALL_GAMES if config.get("enabled", {}).get(g, True)]


def get_all_games_status() -> list[dict]:
    """Return all games with their enabled/disabled status and metadata."""
    config = _load()
    result = []
    for g in ALL_GAMES:
        meta = GAME_META.get(g, {"name": g, "icon": "🎮"})
        result.append({
            "id": g,
            "name": meta["name"],
            "icon": meta["icon"],
            "enabled": config.get("enabled", {}).get(g, True),
        })
    return result


def toggle_game(game_id: str, enabled: bool) -> bool:
    """Toggle a game on or off. Returns True if successful."""
    if game_id not in ALL_GAMES:
        return False
    config = _load()
    if "enabled" not in config:
        config["enabled"] = {g: True for g in ALL_GAMES}
    config["enabled"][game_id] = enabled
    _save(config)
    return True
