"""Tests for YAML feed loader and validation."""

import pytest

from app.templates.feed_loader import (
    load_and_validate,
    load_skills,
    load_templates,
    get_skill_map,
    get_templates_by_chapter,
    get_templates_by_skill,
    get_template_by_id,
    SkillDef,
    TemplateDef,
)


class TestLoadSkills:
    def test_loads_skills_yaml(self):
        feed = load_skills()
        assert len(feed.skills) > 0, "Should load at least one skill"

    def test_skills_have_required_fields(self):
        feed = load_skills()
        for s in feed.skills:
            assert isinstance(s, SkillDef)
            assert s.code
            assert s.chapter in (5, 6, 7, 8)
            assert s.name

    def test_skill_codes_unique(self):
        feed = load_skills()
        codes = [s.code for s in feed.skills]
        assert len(codes) == len(set(codes)), "Skill codes must be unique"

    def test_expected_chapters(self):
        feed = load_skills()
        chapters = {s.chapter for s in feed.skills}
        assert 5 in chapters
        assert 6 in chapters
        assert 7 in chapters
        assert 8 in chapters


class TestLoadTemplates:
    def test_loads_templates_yaml(self):
        feed = load_templates()
        assert len(feed.templates) > 0, "Should load at least one template"

    def test_templates_have_required_fields(self):
        feed = load_templates()
        for t in feed.templates:
            assert isinstance(t, TemplateDef)
            assert t.id
            assert t.chapter in (5, 6, 7, 8)
            assert t.skill
            assert t.prompt
            assert t.marking

    def test_template_ids_unique(self):
        feed = load_templates()
        ids = [t.id for t in feed.templates]
        assert len(ids) == len(set(ids)), "Template IDs must be unique"


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
        # Ensure feeds are loaded first
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
