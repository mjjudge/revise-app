"""Tests for the Minsterworth OS map templates, fixed generator, map_image asset,
keyword_any marker, and gridref_6fig tolerance updates."""

import random

import pytest

from app.services.generators import generate_param
from app.services.marking import mark, MarkResult
from app.services.assets import render_assets
from app.templates.feed_loader import load_templates, load_skills, clear_cache


# ===================================================================
# Fixed generator tests
# ===================================================================


class TestFixedGenerator:
    """The 'fixed' generator must return the value as-is."""

    def _gen(self, spec: dict, seed: int = 42, ctx: dict | None = None):
        rng = random.Random(seed)
        return generate_param(rng, spec, ctx or {})

    def test_fixed_string(self):
        result = self._gen({"gen": "fixed", "value": "hello"})
        assert result == "hello"

    def test_fixed_dict(self):
        result = self._gen({"gen": "fixed", "value": {"correct": "A", "distractors": ["B", "C"]}})
        assert result == {"correct": "A", "distractors": ["B", "C"]}

    def test_fixed_list(self):
        result = self._gen({"gen": "fixed", "value": ["772175", "778177"]})
        assert result == ["772175", "778177"]

    def test_fixed_int(self):
        result = self._gen({"gen": "fixed", "value": 42})
        assert result == 42

    def test_fixed_deterministic(self):
        spec = {"gen": "fixed", "value": "same"}
        a = self._gen(spec, seed=1)
        b = self._gen(spec, seed=999)
        assert a == b  # Always the same regardless of seed


# ===================================================================
# Map image asset renderer tests
# ===================================================================


class TestMapImageAsset:
    """The map_image asset kind must render an <img> tag."""

    def test_renders_img_tag(self):
        specs = [{"kind": "map_image", "id": "map", "src": "/images/test.png", "alt": "Test map"}]
        result = render_assets(specs, {})
        html = result[0]["html"]
        assert '<img' in html
        assert '/images/test.png' in html
        assert 'Test map' in html

    def test_default_alt(self):
        specs = [{"kind": "map_image", "id": "map", "src": "/images/test.png"}]
        result = render_assets(specs, {})
        html = result[0]["html"]
        assert '<img' in html
        assert 'alt="' in html

    def test_caption(self):
        specs = [{"kind": "map_image", "id": "map", "src": "/images/test.png",
                  "caption": "My caption"}]
        result = render_assets(specs, {})
        html = result[0]["html"]
        assert 'My caption' in html


# ===================================================================
# keyword_any marker tests
# ===================================================================


class TestKeywordAnyMarker:
    """keyword_any should accept answers matching any accepted keyword."""

    def test_exact_match(self):
        r = mark("Clayhill Wood", "Clayhill Wood", {"mode": "keyword_any"})
        assert r.correct
        assert r.score == 1.0

    def test_case_insensitive(self):
        r = mark("clayhill wood", "Clayhill Wood", {"mode": "keyword_any"})
        assert r.correct

    def test_substring_match(self):
        r = mark("It is Clayhill Wood nearby", "Clayhill Wood", {"mode": "keyword_any"})
        assert r.correct

    def test_list_of_accepted(self):
        r = mark("Long Brook", ["Long Brook", "Longbrook"], {"mode": "keyword_any"})
        assert r.correct

    def test_wrong_answer(self):
        r = mark("River Thames", "Clayhill Wood", {"mode": "keyword_any"})
        assert not r.correct
        assert r.score == 0.0

    def test_empty_answer(self):
        r = mark("", "Clayhill Wood", {"mode": "keyword_any"})
        assert not r.correct

    def test_accept_any_from_spec(self):
        r = mark("brook", "Long Brook",
                 {"mode": "keyword_any", "accept_any": ["brook", "stream"]})
        assert r.correct


# ===================================================================
# Gridref 6-fig tolerance tests
# ===================================================================


class TestGridref6FigTolerance:
    """gridref_6fig marker should accept answers within tolerance."""

    def test_exact_match_no_tolerance(self):
        r = mark("776172", "776172", {"mode": "gridref_6fig"})
        assert r.correct

    def test_tolerance_1_accept(self):
        r = mark("775171", "776172", {"mode": "gridref_6fig", "tolerance": 1})
        assert r.correct

    def test_tolerance_1_reject(self):
        r = mark("774170", "776172", {"mode": "gridref_6fig", "tolerance": 1})
        assert not r.correct

    def test_multiple_accepted_refs(self):
        r = mark("772175", ["772175", "778177"],
                 {"mode": "gridref_6fig", "tolerance": 1})
        assert r.correct

    def test_multiple_accepted_second_match(self):
        r = mark("778177", ["772175", "778177"],
                 {"mode": "gridref_6fig", "tolerance": 1})
        assert r.correct

    def test_multiple_accepted_reject(self):
        r = mark("800200", ["772175", "778177"],
                 {"mode": "gridref_6fig", "tolerance": 1})
        assert not r.correct

    def test_spec_correct_override(self):
        """spec.correct should be used when present."""
        r = mark("778177", "772175",
                 {"mode": "gridref_6fig", "tolerance": 1,
                  "correct": ["772175", "778177"]})
        assert r.correct


# ===================================================================
# Template loading tests
# ===================================================================


class TestMinsterworthTemplates:
    """All 18 Minsterworth templates must load and validate."""

    @pytest.fixture(autouse=True)
    def load(self):
        clear_cache()
        tpl_feed = load_templates()
        skill_feed = load_skills()
        self.templates = tpl_feed.templates
        self.skills = skill_feed.skills
        self.minst = [t for t in self.templates if t.id.startswith("minsterworth_")]

    def test_18_templates_loaded(self):
        assert len(self.minst) == 18, (
            f"Expected 18 Minsterworth templates, got {len(self.minst)}: "
            + ", ".join(t.id for t in self.minst)
        )

    def test_all_geography_subject(self):
        for t in self.minst:
            assert t.subject == "geography", f"{t.id} subject: {t.subject}"

    def test_all_maps_unit(self):
        for t in self.minst:
            assert t.unit == "maps", f"{t.id} unit: {t.unit}"

    def test_all_have_map_asset(self):
        for t in self.minst:
            kinds = [a.kind for a in t.assets]
            assert "map_image" in kinds, f"{t.id} missing map_image asset"

    def test_skills_exist(self):
        skill_codes = {s.code for s in self.skills}
        for t in self.minst:
            assert t.skill in skill_codes, f"{t.id} skill {t.skill} not in skills"

    @pytest.mark.parametrize("tpl_id", [
        "minsterworth_compass_river_v1",
        "minsterworth_compass_village_v1",
        "minsterworth_compass_clayhill_v1",
        "minsterworth_symbol_fb_v1",
        "minsterworth_symbol_sch_v1",
        "minsterworth_features_v1",
        "minsterworth_woodland_v1",
        "minsterworth_watercourse_v1",
        "minsterworth_transport_v1",
        "minsterworth_gridref4_school_v1",
        "minsterworth_gridref4_cornham_v1",
        "minsterworth_gridref6_school_v1",
        "minsterworth_gridref6_fb_v1",
        "minsterworth_bearing_sch_wood_v1",
        "minsterworth_bearing_sch_cornham_v1",
        "minsterworth_relief_steep_v1",
        "minsterworth_relief_landform_v1",
        "minsterworth_settlement_v1",
    ])
    def test_template_exists(self, tpl_id):
        ids = [t.id for t in self.minst]
        assert tpl_id in ids


# ===================================================================
# Bearing tolerance tests
# ===================================================================


class TestBearingTolerance:
    """bearing_3digit marker should accept answers within tolerance_degrees."""

    def test_exact(self):
        r = mark("075", 75, {"mode": "bearing_3digit", "tolerance_degrees": 5})
        assert r.correct

    def test_within_tolerance(self):
        r = mark("080", 75, {"mode": "bearing_3digit", "tolerance_degrees": 5})
        assert r.correct

    def test_outside_tolerance(self):
        r = mark("085", 75, {"mode": "bearing_3digit", "tolerance_degrees": 5})
        assert not r.correct
