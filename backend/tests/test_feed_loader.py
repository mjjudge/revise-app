"""Tests for YAML feed loader and validation (multi-subject)."""

import pytest

from app.templates.feed_loader import (
    clear_cache,
    load_and_validate,
    load_skills,
    load_templates,
    get_skill_map,
    get_subjects,
    get_templates_by_chapter,
    get_templates_by_skill,
    get_templates_by_subject,
    get_templates_by_unit,
    get_template_by_id,
    get_units_for_subject,
    SkillDef,
    TemplateDef,
)


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Clear the feed-loader cache before every test."""
    clear_cache()
    yield
    clear_cache()


class TestLoadSkills:
    def test_loads_skills_yaml(self):
        feed = load_skills()
        assert len(feed.skills) > 0, "Should load at least one skill"

    def test_skills_have_required_fields(self):
        feed = load_skills()
        for s in feed.skills:
            assert isinstance(s, SkillDef)
            assert s.code
            assert s.name
            # Every skill must have a subject (auto-mapped for maths)
            assert s.subject, f"Skill '{s.code}' missing subject"

    def test_skill_codes_unique(self):
        feed = load_skills()
        codes = [s.code for s in feed.skills]
        assert len(codes) == len(set(codes)), "Skill codes must be unique"

    def test_expected_maths_chapters(self):
        feed = load_skills()
        maths = [s for s in feed.skills if s.subject == "maths"]
        chapters = {s.chapter for s in maths}
        assert 5 in chapters
        assert 6 in chapters
        assert 7 in chapters
        assert 8 in chapters

    def test_geography_skills_loaded(self):
        feed = load_skills()
        geog = [s for s in feed.skills if s.subject == "geography"]
        assert len(geog) > 0, "Should load geography skills"
        for s in geog:
            assert s.unit, f"Geography skill '{s.code}' missing unit"
            assert s.chapter is None, "Geography skills should have no chapter"

    def test_maths_auto_mapped_unit(self):
        feed = load_skills()
        maths = [s for s in feed.skills if s.subject == "maths"]
        for s in maths:
            assert s.unit is not None, f"Maths skill '{s.code}' should have auto-mapped unit"


class TestLoadTemplates:
    def test_loads_templates_yaml(self):
        feed = load_templates()
        assert len(feed.templates) > 0, "Should load at least one template"

    def test_templates_have_required_fields(self):
        feed = load_templates()
        for t in feed.templates:
            assert isinstance(t, TemplateDef)
            assert t.id
            assert t.skill
            assert t.prompt
            assert t.marking
            # Every template gets a subject (auto-mapped for maths)
            assert t.subject, f"Template '{t.id}' missing subject"

    def test_maths_templates_have_chapter(self):
        feed = load_templates()
        maths = [t for t in feed.templates if t.subject == "maths"]
        for t in maths:
            assert t.chapter in (5, 6, 7, 8), f"Maths template '{t.id}' has bad chapter"

    def test_template_ids_unique(self):
        feed = load_templates()
        ids = [t.id for t in feed.templates]
        assert len(ids) == len(set(ids)), "Template IDs must be unique"

    def test_geography_templates_loaded(self):
        feed = load_templates()
        geog = [t for t in feed.templates if t.subject == "geography"]
        assert len(geog) > 0, "Should load geography templates"
        for t in geog:
            assert t.unit, f"Geography template '{t.id}' missing unit"


class TestCrossValidation:
    def test_validate_feeds_succeeds(self):
        """Should load and cross-validate without errors."""
        skills_feed, templates_feed = load_and_validate()
        assert len(skills_feed.skills) > 0
        assert len(templates_feed.templates) > 0

    def test_all_template_skills_exist(self):
        """Every template skill code must match a skill definition."""
        skills_feed, templates_feed = load_and_validate()
        skill_codes = {s.code for s in skills_feed.skills}
        for t in templates_feed.templates:
            assert t.skill in skill_codes, f"Template {t.id} references unknown skill {t.skill}"


class TestLookupHelpers:
    def test_get_skill_map(self):
        load_and_validate()
        sm = get_skill_map()
        assert isinstance(sm, dict)
        assert len(sm) > 0
        for code, skill in sm.items():
            assert code == skill.code

    def test_get_templates_by_chapter(self):
        load_and_validate()
        ch5 = get_templates_by_chapter(5)
        assert len(ch5) > 0
        for t in ch5:
            assert t.chapter == 5

    def test_get_templates_by_skill(self):
        load_and_validate()
        ts = get_templates_by_skill("stats.mean.basic")
        assert len(ts) > 0
        for t in ts:
            assert t.skill == "stats.mean.basic"

    def test_get_template_by_id(self):
        load_and_validate()
        t = get_template_by_id("ch5_mean_from_list_v1")
        assert t is not None
        assert t.id == "ch5_mean_from_list_v1"

    def test_get_template_by_id_not_found(self):
        load_and_validate()
        assert get_template_by_id("nonexistent_template") is None

    def test_get_templates_by_subject(self):
        load_and_validate()
        maths = get_templates_by_subject("maths")
        assert len(maths) > 0
        for t in maths:
            assert t.subject == "maths"

    def test_get_templates_by_unit(self):
        load_and_validate()
        data = get_templates_by_unit("maths", "data")
        assert len(data) > 0
        for t in data:
            assert t.subject == "maths"
            assert t.unit == "data"

    def test_get_subjects(self):
        load_and_validate()
        subjects = get_subjects()
        assert "maths" in subjects
        assert "geography" in subjects

    def test_get_units_for_subject(self):
        load_and_validate()
        maths_units = get_units_for_subject("maths")
        assert "data" in maths_units
        assert "algebra" in maths_units
        assert "calculation" in maths_units
        assert "probability" in maths_units

        geog_units = get_units_for_subject("geography")
        assert "maps" in geog_units
