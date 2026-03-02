"""Tests for question repeat-prevention within a quest session."""

import pytest
from collections import Counter
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession
from app.models.question import QuestionInstance
from app.services.questions import _select_template, _exclude_recent
from app.templates.feed_loader import get_templates_by_skill, get_templates_by_unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="kid")
def kid_fixture(session):
    user = User(
        display_name="Test",
        role=Role.kid,
        pin_hash="$2b$12$fake",
        xp=0,
        gold=0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# _exclude_recent tests
# ---------------------------------------------------------------------------

class TestExcludeRecent:
    """Test the _exclude_recent helper."""

    def test_empty_exclude_set_returns_all(self):
        """With no exclusions, full list is returned."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        assert len(_exclude_recent(templates, set())) == len(templates)

    def test_excludes_matching_ids(self):
        """Templates whose ids are in the exclude set are removed."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        assert len(templates) >= 2, "Need ≥2 templates for this test"
        exclude = {templates[0].id}
        result = _exclude_recent(templates, exclude)
        assert all(t.id != templates[0].id for t in result)
        assert len(result) == len(templates) - 1

    def test_fallback_when_all_excluded(self):
        """When all templates are excluded, returns the full list (fallback)."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        all_ids = {t.id for t in templates}
        result = _exclude_recent(templates, all_ids)
        # Should fall back to unfiltered list
        assert len(result) == len(templates)


# ---------------------------------------------------------------------------
# _select_template avoids recently-seen templates
# ---------------------------------------------------------------------------

class TestSelectTemplateExclusion:
    """Test that _select_template respects exclude_template_ids."""

    def test_skill_query_excludes(self, session, kid):
        """Skill-mode selection avoids excluded templates."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        if len(templates) < 2:
            pytest.skip("Need ≥2 compass_points templates")

        # Exclude all but one template
        keep = templates[0]
        exclude = {t.id for t in templates if t.id != keep.id}
        # Should always pick the one remaining
        for _ in range(10):
            picked = _select_template(
                session, kid,
                skill="geog.maps.compass_points", chapter=None,
                template_id=None,
                exclude_template_ids=exclude,
            )
            assert picked.id == keep.id

    def test_unit_query_excludes(self, session, kid):
        """Unit-mode selection avoids excluded templates."""
        templates = get_templates_by_unit("geography", "maps")
        if len(templates) < 2:
            pytest.skip("Need ≥2 geography/maps templates")

        keep = templates[0]
        exclude = {t.id for t in templates if t.id != keep.id}
        for _ in range(10):
            picked = _select_template(
                session, kid,
                skill=None, chapter=None,
                subject="geography", unit="maps",
                template_id=None,
                exclude_template_ids=exclude,
            )
            assert picked.id == keep.id

    def test_explicit_template_id_ignores_exclude(self, session, kid):
        """When a specific template_id is requested, exclusions are ignored."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        target = templates[0]
        picked = _select_template(
            session, kid,
            skill=None, chapter=None,
            template_id=target.id,
            exclude_template_ids={target.id},
        )
        assert picked.id == target.id


# ---------------------------------------------------------------------------
# Statistical evidence: repeats decrease with exclusion
# ---------------------------------------------------------------------------

class TestRepeatReduction:
    """Verify that excluding used templates reduces consecutive repeats."""

    def test_repeat_rate_lower_with_exclusion(self, session, kid):
        """Over many draws, exclusion should produce fewer back-to-back repeats."""
        templates = get_templates_by_skill("geog.maps.compass_points")
        if len(templates) < 3:
            pytest.skip("Need ≥3 templates for statistical test")

        n_draws = 60

        # Without exclusion
        picks_no_excl = []
        for _ in range(n_draws):
            t = _select_template(
                session, kid,
                skill="geog.maps.compass_points", chapter=None,
                template_id=None,
            )
            picks_no_excl.append(t.id)

        # With exclusion (exclude last pick only)
        picks_excl = []
        last_id: str | None = None
        for _ in range(n_draws):
            excl = {last_id} if last_id else set()
            t = _select_template(
                session, kid,
                skill="geog.maps.compass_points", chapter=None,
                template_id=None,
                exclude_template_ids=excl,
            )
            picks_excl.append(t.id)
            last_id = t.id

        # Count back-to-back repeats
        def back_to_back(picks):
            return sum(1 for a, b in zip(picks, picks[1:]) if a == b)

        repeats_with_excl = back_to_back(picks_excl)
        # With ≥3 templates and single-exclusion, back-to-back should be 0
        assert repeats_with_excl == 0, (
            f"Expected 0 back-to-back repeats with exclusion, got {repeats_with_excl}"
        )
