"""Tangram puzzle CRUD — stores puzzles as JSON files in data/tangram/."""

import json
import os
import re
import shutil
from pathlib import Path

DATA_DIR = Path("/data/tangram")
SEED_DIR = Path(__file__).resolve().parent.parent / "static" / "tangram"

# Piece templates used when creating fresh puzzles
DEFAULT_PIECES = [
    {
        "id": "big_tri_1",
        "polygon": [[0, 0], [100, 0], [0, 100]],
        "color": "#ef4444",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "big_tri_2",
        "polygon": [[0, 0], [100, 0], [0, 100]],
        "color": "#f59e0b",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "med_tri",
        "polygon": [[0, 0], [70, 0], [0, 70]],
        "color": "#10b981",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "small_tri_1",
        "polygon": [[0, 0], [50, 0], [0, 50]],
        "color": "#3b82f6",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "small_tri_2",
        "polygon": [[0, 0], [50, 0], [0, 50]],
        "color": "#8b5cf6",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "square",
        "polygon": [[0, 0], [50, 0], [50, 50], [0, 50]],
        "color": "#ec4899",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
    {
        "id": "parallelogram",
        "polygon": [[0, 0], [50, 0], [100, 50], [50, 50]],
        "color": "#14b8a6",
        "snap": {"distPx": 22, "rotDeg": 12},
        "lockOnSnap": True,
    },
]

DEFAULT_BOARD = {
    "width": 400,
    "height": 420,
    "trayArea": {"x": 0, "y": 300, "w": 400, "h": 120},
    "playArea": {"x": 50, "y": 10, "w": 300, "h": 280},
}

DEFAULT_RULES = {
    "allowFlip": False,
    "rotationStepDeg": 15,
    "completion": "target_pose",
}


def _safe_id(name: str) -> str:
    """Create a filesystem-safe ID from a puzzle name."""
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_").replace("-", "_"))


def ensure_data_dir() -> None:
    """Create data/tangram/ and seed defaults if empty."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not any(DATA_DIR.glob("*.json")) and SEED_DIR.is_dir():
        for f in SEED_DIR.glob("*.json"):
            shutil.copy2(f, DATA_DIR / f.name)


def list_puzzles() -> list[dict]:
    """Return list of {id, title} for all puzzles."""
    ensure_data_dir()
    puzzles = []
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            puzzles.append({"id": data.get("id", f.stem), "title": data.get("title", f.stem)})
        except (json.JSONDecodeError, KeyError):
            continue
    return puzzles


def get_puzzle(puzzle_id: str) -> dict | None:
    """Load a single puzzle by ID."""
    ensure_data_dir()
    path = DATA_DIR / f"{puzzle_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def save_puzzle(puzzle: dict) -> str:
    """Save (create or update) a puzzle. Returns the puzzle ID."""
    ensure_data_dir()
    pid = puzzle.get("id") or _safe_id(puzzle.get("title", "untitled"))
    puzzle["id"] = pid
    path = DATA_DIR / f"{pid}.json"
    path.write_text(json.dumps(puzzle, indent=2))
    return pid


def delete_puzzle(puzzle_id: str) -> bool:
    """Delete a puzzle. Returns True if it existed."""
    path = DATA_DIR / f"{puzzle_id}.json"
    if path.is_file():
        path.unlink()
        return True
    return False


def blank_puzzle(title: str) -> dict:
    """Create a blank puzzle scaffold with pieces in the tray area."""
    pid = _safe_id(title)
    start_positions = [
        {"x": 10, "y": 310}, {"x": 120, "y": 310}, {"x": 230, "y": 320},
        {"x": 310, "y": 315}, {"x": 360, "y": 315}, {"x": 300, "y": 350},
        {"x": 120, "y": 350},
    ]
    pieces = []
    for i, tmpl in enumerate(DEFAULT_PIECES):
        p = dict(tmpl)
        pos = start_positions[i]
        p["startPose"] = {"position": pos, "rotationDeg": 0}
        # Default target = same as start (user will drag to set)
        p["targetPose"] = {"position": dict(pos), "rotationDeg": 0}
        pieces.append(p)
    return {
        "id": pid,
        "title": title,
        "board": dict(DEFAULT_BOARD),
        "rules": dict(DEFAULT_RULES),
        "pieces": pieces,
    }
