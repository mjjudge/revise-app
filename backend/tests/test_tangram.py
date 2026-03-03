"""Tests for tangram puzzle service (CRUD, interchangeable pieces, blank scaffolds)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.tangram_service import (
    list_puzzles,
    get_puzzle,
    save_puzzle,
    delete_puzzle,
    blank_puzzle,
    ensure_data_dir,
    DEFAULT_PIECES,
)


@pytest.fixture(autouse=True)
def _temp_tangram_dir(tmp_path):
    """Redirect tangram storage to a temp directory for each test."""
    data_dir = tmp_path / "tangram"
    seed_dir = tmp_path / "seed_tangram"
    seed_dir.mkdir()
    # Create a minimal seed puzzle
    (seed_dir / "test_seed.json").write_text(json.dumps({
        "id": "test_seed",
        "title": "Test Seed",
        "board": {"width": 400, "height": 420,
                  "trayArea": {"x": 0, "y": 300, "w": 400, "h": 120},
                  "playArea": {"x": 50, "y": 10, "w": 300, "h": 280}},
        "rules": {"rotationStepDeg": 15, "completion": "target_pose"},
        "pieces": [],
    }))
    with patch("app.services.tangram_service.DATA_DIR", data_dir), \
         patch("app.services.tangram_service.SEED_DIR", seed_dir):
        yield data_dir


class TestEnsureDataDir:
    def test_seeds_copied_on_first_run(self, _temp_tangram_dir):
        """When data dir is empty, seed puzzles are copied."""
        ensure_data_dir()
        assert (_temp_tangram_dir / "test_seed.json").is_file()

    def test_no_overwrite_on_second_run(self, _temp_tangram_dir):
        """Seeding only happens when dir has no JSON files."""
        ensure_data_dir()
        # Modify the seeded file
        p = _temp_tangram_dir / "test_seed.json"
        data = json.loads(p.read_text())
        data["title"] = "Modified"
        p.write_text(json.dumps(data))
        # Run ensure again — should NOT overwrite
        ensure_data_dir()
        data2 = json.loads(p.read_text())
        assert data2["title"] == "Modified"


class TestListPuzzles:
    def test_lists_seeded_puzzles(self, _temp_tangram_dir):
        """list_puzzles returns seeded puzzles."""
        result = list_puzzles()
        assert len(result) >= 1
        assert any(p["id"] == "test_seed" for p in result)

    def test_empty_when_no_puzzles(self, _temp_tangram_dir):
        """list_puzzles returns empty list when no puzzles and no seed dir."""
        ensure_data_dir()
        for f in _temp_tangram_dir.glob("*.json"):
            f.unlink()
        # Patch seed dir to nonexistent so it won't re-seed
        with patch("app.services.tangram_service.SEED_DIR", _temp_tangram_dir / "noseed"):
            result = list_puzzles()
        assert result == []


class TestGetPuzzle:
    def test_get_existing_puzzle(self, _temp_tangram_dir):
        """get_puzzle returns the puzzle data."""
        result = get_puzzle("test_seed")
        assert result is not None
        assert result["title"] == "Test Seed"

    def test_get_nonexistent_puzzle(self, _temp_tangram_dir):
        """get_puzzle returns None for missing puzzle."""
        result = get_puzzle("nonexistent_xyz")
        assert result is None


class TestSavePuzzle:
    def test_save_new_puzzle(self, _temp_tangram_dir):
        """save_puzzle writes a new JSON file."""
        puzzle = {"id": "my_new", "title": "My New", "pieces": []}
        pid = save_puzzle(puzzle)
        assert pid == "my_new"
        assert (_temp_tangram_dir / "my_new.json").is_file()
        loaded = get_puzzle("my_new")
        assert loaded["title"] == "My New"

    def test_save_generates_id_from_title(self, _temp_tangram_dir):
        """save_puzzle auto-generates ID from title when id is empty."""
        puzzle = {"title": "Cool Puzzle!", "pieces": []}
        pid = save_puzzle(puzzle)
        assert pid == "cool_puzzle"

    def test_save_overwrites_existing(self, _temp_tangram_dir):
        """save_puzzle overwrites an existing puzzle."""
        save_puzzle({"id": "test_seed", "title": "Updated Title", "pieces": []})
        loaded = get_puzzle("test_seed")
        assert loaded["title"] == "Updated Title"


class TestDeletePuzzle:
    def test_delete_existing(self, _temp_tangram_dir):
        """delete_puzzle removes the file and returns True."""
        ensure_data_dir()
        assert delete_puzzle("test_seed") is True
        # Patch seed dir so it won't re-seed
        with patch("app.services.tangram_service.SEED_DIR", _temp_tangram_dir / "noseed"):
            assert get_puzzle("test_seed") is None

    def test_delete_nonexistent(self, _temp_tangram_dir):
        """delete_puzzle returns False for missing puzzle."""
        assert delete_puzzle("does_not_exist") is False


class TestBlankPuzzle:
    def test_blank_has_7_pieces(self):
        """blank_puzzle creates a puzzle with 7 pieces."""
        p = blank_puzzle("Fox")
        assert len(p["pieces"]) == 7

    def test_blank_id_from_title(self):
        """blank_puzzle generates safe ID."""
        p = blank_puzzle("My Cool Shape")
        assert p["id"] == "my_cool_shape"

    def test_blank_has_correct_structure(self):
        """blank_puzzle has board, rules, and piece structure."""
        p = blank_puzzle("Test")
        assert "board" in p
        assert "rules" in p
        assert p["board"]["width"] == 400
        for piece in p["pieces"]:
            assert "polygon" in piece
            assert "color" in piece
            assert "startPose" in piece
            assert "targetPose" in piece
            assert "snap" in piece

    def test_blank_poses_include_flipped(self):
        """blank_puzzle start and target poses include flipped=False."""
        p = blank_puzzle("FlipTest")
        for piece in p["pieces"]:
            assert piece["startPose"]["flipped"] is False
            assert piece["targetPose"]["flipped"] is False

    def test_blank_rules_include_allow_flip(self):
        """blank_puzzle rules include allowFlip."""
        p = blank_puzzle("RuleTest")
        assert "allowFlip" in p["rules"]

    def test_parallelogram_is_non_symmetrical(self):
        """The parallelogram is the only non-symmetrical piece (can benefit from flip)."""
        polys = {p["id"]: p["polygon"] for p in DEFAULT_PIECES}
        para = polys["parallelogram"]
        # Verify it's non-symmetrical: mirroring the X coords produces different polygon
        cx = sum(v[0] for v in para) / len(para)
        mirrored = sorted([[2 * cx - v[0], v[1]] for v in para])
        original = sorted(para)
        assert mirrored != original, "Parallelogram should be non-symmetrical"

    def test_save_preserves_flipped_state(self, _temp_tangram_dir):
        """save_puzzle preserves flipped flag in target poses."""
        puzzle = blank_puzzle("FlipSave")
        # Simulate setting one piece as flipped via the editor
        puzzle["pieces"][6]["targetPose"]["flipped"] = True  # parallelogram
        pid = save_puzzle(puzzle)
        loaded = get_puzzle(pid)
        assert loaded["pieces"][6]["targetPose"]["flipped"] is True
        assert loaded["pieces"][0]["targetPose"]["flipped"] is False

    def test_default_pieces_count(self):
        """DEFAULT_PIECES has 7 entries."""
        assert len(DEFAULT_PIECES) == 7

    def test_interchangeable_shapes(self):
        """Two big triangles and two small triangles have same polygon."""
        polys = {p["id"]: p["polygon"] for p in DEFAULT_PIECES}
        assert polys["big_tri_1"] == polys["big_tri_2"]
        assert polys["small_tri_1"] == polys["small_tri_2"]
        # Medium triangle is different from big and small
        assert polys["med_tri"] != polys["big_tri_1"]
        assert polys["med_tri"] != polys["small_tri_1"]
