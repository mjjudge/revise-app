"""Tests for geography generators, marking modes, and answer computation."""

import json
import random

import pytest

from app.services.generators import generate_param
from app.services.marking import mark, MarkResult


# ===================================================================
# Geography generator tests
# ===================================================================


class TestGeographyGeneratorDeterminism:
    """Geography generators must produce same output for same seed."""

    def _gen(self, spec: dict, seed: int = 42, ctx: dict | None = None) -> any:
        rng = random.Random(seed)
        return generate_param(rng, spec, ctx or {})

    # ── Knowledge MCQ ────────────────────────────

    def test_knowledge_mcq_deterministic(self):
        spec = {"gen": "geog_knowledge_mcq", "topic": "troposphere"}
        a = self._gen(spec, seed=42)
        b = self._gen(spec, seed=42)
        assert a == b
        assert "correct" in a
        assert "distractors" in a
        assert len(a["distractors"]) >= 2

    @pytest.mark.parametrize("topic", ["troposphere", "depression", "climate_impacts", "heatwave"])
    def test_knowledge_mcq_all_topics(self, topic):
        spec = {"gen": "geog_knowledge_mcq", "topic": topic}
        result = self._gen(spec, seed=99)
        assert result["correct"] not in result["distractors"]

    # ── Matching-set generators ────────────────────────────

    @pytest.mark.parametrize("gen_name,pick", [
        ("instruments_set", 5),
        ("uk_air_masses_set", 4),
        ("cloud_set", 3),
        ("symbol_set", 5),
        ("water_cycle_set", 4),
        ("continents_oceans_set", 6),
    ])
    def test_matching_set_structure(self, gen_name, pick):
        spec = {"gen": gen_name, "pick": pick}
        result = self._gen(spec, seed=42)
        assert "left" in result
        assert "right" in result
        assert "correct_mapping" in result
        assert len(result["left"]) == pick
        assert len(result["right"]) == pick
        assert len(result["correct_mapping"]) == pick
        # Verify correct_mapping maps left → right
        for k, v in result["correct_mapping"].items():
            assert k in result["left"]
            assert v in result["right"]

    def test_matching_set_deterministic(self):
        spec = {"gen": "instruments_set", "pick": 5}
        a = self._gen(spec, seed=123)
        b = self._gen(spec, seed=123)
        assert a == b

    # ── Map scale ────────────────────────────

    def test_map_scale(self):
        spec = {"gen": "map_scale"}
        result = self._gen(spec, seed=42)
        assert "ratio" in result
        assert "text" in result
        assert result["ratio"] in (25000, 50000, 100000)

    # ── Grid map ────────────────────────────

    def test_grid_map_basic(self):
        spec = {
            "gen": "grid_map_with_features",
            "grid_size": 8,
            "feature_count": 5,
            "feature_names": ["Farm", "Bridge", "School", "Wood", "Lake"],
        }
        result = self._gen(spec, seed=42)
        assert "features" in result
        assert len(result["features"]) == 5
        assert "grid_ref_4fig" in result
        assert "grid_ref_6fig" in result
        assert "east_offset" in result
        assert "north_offset" in result
        # Each feature should have a 4-fig ref
        for name in ["Farm", "Bridge", "School", "Wood", "Lake"]:
            ref = result["grid_ref_4fig"][name]
            assert len(ref) == 4, f"4-fig ref for {name} is '{ref}'"

    def test_grid_map_6fig(self):
        spec = {
            "gen": "grid_map_with_features",
            "grid_size": 8,
            "feature_count": 3,
            "feature_names": ["A", "B", "C"],
            "precise": True,
        }
        result = self._gen(spec, seed=42)
        for name in ["A", "B", "C"]:
            ref = result["grid_ref_6fig"][name]
            assert len(ref) == 6, f"6-fig ref for {name} is '{ref}'"

    def test_grid_map_deterministic(self):
        spec = {
            "gen": "grid_map_with_features",
            "grid_size": 8,
            "feature_count": 4,
            "feature_names": ["X", "Y", "Z", "W"],
        }
        a = self._gen(spec, seed=77)
        b = self._gen(spec, seed=77)
        assert a == b

    # ── Compass direction MCQ ────────────────────────────

    def test_compass_direction_mcq(self):
        # Need map in context first
        map_spec = {
            "gen": "grid_map_with_features",
            "grid_size": 8,
            "feature_count": 3,
            "feature_names": ["Farm", "Bridge", "School"],
        }
        map_data = self._gen(map_spec, seed=42)
        ctx = {"map": map_data, "from_feature": "Farm", "to_feature": "Bridge"}
        spec = {"gen": "compass_direction_mcq", "map_ref": "map", "from_name": "from_feature", "to_name": "to_feature"}
        result = self._gen(spec, seed=42, ctx=ctx)
        assert "correct" in result
        assert "distractors" in result
        assert result["correct"] in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    # ── Climograph dataset ────────────────────────────

    @pytest.mark.parametrize("climate_type", ["temperate", "tropical", "mediterranean", "polar", "tropical_dry"])
    def test_climograph_dataset(self, climate_type):
        spec = {"gen": "climograph_dataset", "climate_type": climate_type}
        result = self._gen(spec, seed=42)
        assert len(result["months"]) == 12
        assert len(result["temp_c"]) == 12
        assert len(result["rain_mm"]) == 12
        assert result["climate_type"] == climate_type

    def test_climograph_random_type(self):
        spec = {"gen": "climograph_dataset", "climate_type": "random"}
        result = self._gen(spec, seed=42)
        assert result["climate_type"] in ["temperate", "tropical", "mediterranean", "polar", "tropical_dry"]

    # ── Contour map ────────────────────────────

    @pytest.mark.parametrize("style", ["hill", "landform", "cross_section"])
    def test_synthetic_contour_map(self, style):
        spec = {"gen": "synthetic_contour_map", "style": style}
        result = self._gen(spec, seed=42)
        assert "contours" in result
        assert "interval" in result
        assert "marked_point" in result
        if style == "landform":
            assert "mcq" in result
        if style == "cross_section":
            assert "mcq" in result
            assert "cross_sections" in result
            assert "line_ab" in result

    # ── Isobar chart ────────────────────────────

    def test_isobar_chart(self):
        spec = {"gen": "isobar_chart_data"}
        result = self._gen(spec, seed=42)
        assert "centers" in result
        assert "mcq" in result
        assert len(result["centers"]) == 4

    # ── Rainfall diagram ────────────────────────────

    def test_rainfall_diagram(self):
        spec = {"gen": "rainfall_diagram_data"}
        result = self._gen(spec, seed=42)
        assert "type" in result
        assert "mcq" in result
        assert result["type"] in ["relief", "convectional", "frontal"]

    # ── pick_one ────────────────────────────

    def test_pick_one(self):
        ctx = {"map": {"feature_names": ["A", "B", "C"]}}
        spec = {"gen": "pick_one", "from": "map.feature_names"}
        result = self._gen(spec, seed=42, ctx=ctx)
        assert result in ["A", "B", "C"]

    # ── pick_one_distinct ────────────────────────────

    def test_pick_one_distinct(self):
        ctx = {"map": {"feature_names": ["A", "B", "C"]}, "from_feature": "A"}
        spec = {"gen": "pick_one_distinct", "from": "map.feature_names", "not_equal_to": "from_feature"}
        result = self._gen(spec, seed=42, ctx=ctx)
        assert result in ["B", "C"]
        assert result != "A"

    # ── from_object ────────────────────────────

    def test_from_object(self):
        ctx = {"scale": {"ratio": 50000, "text": "1 : 50,000"}}
        spec = {"gen": "from_object", "object": "scale", "field": "text"}
        result = self._gen(spec, seed=42, ctx=ctx)
        assert result == "1 : 50,000"


# ===================================================================
# Geography marking mode tests
# ===================================================================


class TestGridref4fig:
    def test_correct(self):
        r = mark("1523", "1523", {"mode": "gridref_4fig"})
        assert r.correct

    def test_with_spaces(self):
        r = mark("15 23", "1523", {"mode": "gridref_4fig"})
        assert r.correct

    def test_wrong(self):
        r = mark("1524", "1523", {"mode": "gridref_4fig"})
        assert not r.correct

    def test_invalid_format(self):
        r = mark("abc", "1523", {"mode": "gridref_4fig"})
        assert not r.correct
        assert "4-figure" in r.feedback

    def test_too_few_digits(self):
        r = mark("123", "1523", {"mode": "gridref_4fig"})
        assert not r.correct


class TestGridref6fig:
    def test_correct(self):
        r = mark("152234", "152234", {"mode": "gridref_6fig"})
        assert r.correct

    def test_with_spaces(self):
        r = mark("152 234", "152234", {"mode": "gridref_6fig"})
        assert r.correct

    def test_wrong(self):
        r = mark("152235", "152234", {"mode": "gridref_6fig"})
        assert not r.correct

    def test_invalid_format(self):
        r = mark("12345", "152234", {"mode": "gridref_6fig"})
        assert not r.correct
        assert "6-figure" in r.feedback


class TestBearing3digit:
    def test_exact(self):
        r = mark("045", 45, {"mode": "bearing_3digit"})
        assert r.correct

    def test_within_tolerance(self):
        r = mark("047", 45, {"mode": "bearing_3digit", "tolerance_degrees": 2})
        assert r.correct

    def test_outside_tolerance(self):
        r = mark("050", 45, {"mode": "bearing_3digit", "tolerance_degrees": 2})
        assert not r.correct

    def test_with_degree_symbol(self):
        r = mark("045°", 45, {"mode": "bearing_3digit"})
        assert r.correct

    def test_wrapping_360(self):
        """358° should be close to 0°/360°."""
        r = mark("358", 0, {"mode": "bearing_3digit", "tolerance_degrees": 3})
        assert r.correct


class TestGridMatch:
    def test_all_correct(self):
        correct = {"Barometer": "Air pressure", "Thermometer": "Temperature"}
        student = json.dumps({"Barometer": "Air pressure", "Thermometer": "Temperature"})
        r = mark(student, correct, {"mode": "grid_match"})
        assert r.correct
        assert r.score == 1.0

    def test_partial(self):
        correct = {"Barometer": "Air pressure", "Thermometer": "Temperature", "Anemometer": "Wind speed"}
        student = json.dumps({"Barometer": "Air pressure", "Thermometer": "Wind speed", "Anemometer": "Temperature"})
        r = mark(student, correct, {"mode": "grid_match"})
        assert not r.correct
        assert 0 < r.score < 1.0

    def test_case_insensitive(self):
        correct = {"Barometer": "Air pressure"}
        student = json.dumps({"barometer": "air pressure"})
        r = mark(student, correct, {"mode": "grid_match"})
        assert r.correct

    def test_none_correct(self):
        correct = {"Barometer": "Air pressure"}
        student = json.dumps({"Barometer": "Temperature"})
        r = mark(student, correct, {"mode": "grid_match"})
        assert not r.correct
        assert r.score == 0.0

    def test_invalid_json(self):
        r = mark("not json", {"A": "B"}, {"mode": "grid_match"})
        assert not r.correct


class TestLabelMatch:
    def test_alias_works(self):
        correct = {"X": "Y"}
        student = json.dumps({"X": "Y"})
        r = mark(student, correct, {"mode": "label_match"})
        assert r.correct


# ===================================================================
# E2E geography template generation tests
# ===================================================================


class TestGeographyTemplateGeneration:
    """Test that geography templates can be loaded, generated, and answered."""

    def test_geography_templates_loaded(self):
        from app.templates.feed_loader import get_templates_by_subject
        geog = get_templates_by_subject("geography")
        assert len(geog) >= 20, f"Expected at least 20 geography templates, got {len(geog)}"

    def test_geography_units(self):
        from app.templates.feed_loader import get_templates_by_unit
        for unit in ("maps", "weather", "climate", "world"):
            templates = get_templates_by_unit("geography", unit)
            assert len(templates) > 0, f"No templates for geography unit '{unit}'"

    def test_all_geography_templates_generate(self):
        """Every geography template should generate params without error."""
        from app.templates.feed_loader import get_templates_by_subject
        from app.services.questions import _generate_params, _compute_answer
        geog = get_templates_by_subject("geography")
        for tpl in geog:
            seed = 42
            params = _generate_params(tpl, seed)
            assert isinstance(params, dict), f"Template {tpl.id} failed to generate params"
            answer = _compute_answer(tpl, params)
            assert answer is not None, f"Template {tpl.id} failed to compute answer"

    def test_mcq_templates_have_distractors(self):
        """MCQ geography templates should produce valid distractors."""
        from app.templates.feed_loader import get_templates_by_subject
        from app.services.questions import _generate_params
        geog = get_templates_by_subject("geography")
        mcq_templates = [t for t in geog if t.marking.mode.value == "mcq"]
        assert len(mcq_templates) >= 8, f"Expected at least 8 MCQ templates, got {len(mcq_templates)}"
        for tpl in mcq_templates:
            params = _generate_params(tpl, seed=42)
            dist = params.get("distractors", {})
            assert "correct" in dist, f"Template {tpl.id} missing 'correct' in distractors"
            assert len(dist.get("distractors", [])) >= 2, f"Template {tpl.id} needs ≥2 distractors"

    def test_grid_fill_templates_have_pairs(self):
        """Grid fill templates should produce valid matching pairs."""
        from app.templates.feed_loader import get_templates_by_subject
        from app.services.questions import _generate_params
        geog = get_templates_by_subject("geography")
        gf_templates = [t for t in geog if t.marking.mode.value in ("grid_match", "label_match")]
        assert len(gf_templates) >= 6, f"Expected at least 6 grid_fill templates, got {len(gf_templates)}"
        for tpl in gf_templates:
            params = _generate_params(tpl, seed=42)
            pairs = params.get("pairs", {})
            assert "left" in pairs, f"Template {tpl.id} missing 'left' in pairs"
            assert "right" in pairs, f"Template {tpl.id} missing 'right' in pairs"
            assert "correct_mapping" in pairs, f"Template {tpl.id} missing 'correct_mapping'"
