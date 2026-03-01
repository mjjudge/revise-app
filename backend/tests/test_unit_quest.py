"""Tests for unit quest standardisation — unit quests across any subject."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession
from app.services.questions import generate_question, _select_template
from app.templates.feed_loader import get_templates_by_unit


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
        display_name="Anna",
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
# QuestSession model — subject/unit fields
# ---------------------------------------------------------------------------

class TestQuestSessionSubjectUnit:
    def test_create_unit_quest_session(self, session, kid):
        """Unit quest stores subject + unit, chapter defaults to 0."""
        quest = QuestSession(
            user_id=kid.id,
            subject="geography",
            unit="weather",
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        assert quest.id is not None
        assert quest.subject == "geography"
        assert quest.unit == "weather"
        assert quest.chapter == 0
        assert quest.skill is None
        assert quest.total_questions == 10
        assert quest.finished is False

    def test_skill_quest_with_subject(self, session, kid):
        """Skill quest can carry subject/unit context too."""
        quest = QuestSession(
            user_id=kid.id,
            subject="geography",
            unit="weather",
            skill="geo.weather.types",
            total_questions=8,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        assert quest.skill == "geo.weather.types"
        assert quest.subject == "geography"
        assert quest.unit == "weather"

    def test_chapter_quest_still_works(self, session, kid):
        """Maths chapter quests remain unchanged."""
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        assert quest.chapter == 5
        assert quest.subject is None
        assert quest.unit is None

    def test_question_id_tracking(self, session, kid):
        """Question ID tracking works for unit quests."""
        quest = QuestSession(
            user_id=kid.id,
            subject="geography",
            unit="weather",
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        quest.add_question_id(42)
        quest.add_question_id(99)
        assert quest.get_question_ids() == [42, 99]


# ---------------------------------------------------------------------------
# Template selection — unit-based
# ---------------------------------------------------------------------------

class TestUnitTemplateSelection:
    def test_select_template_by_unit(self, session, kid):
        """_select_template picks from unit pool when subject+unit given."""
        templates = get_templates_by_unit("geography", "weather")
        if not templates:
            pytest.skip("No geography weather templates loaded")

        t = _select_template(
            session, kid,
            skill=None,
            chapter=None,
            subject="geography",
            unit="weather",
            template_id=None,
        )
        assert t is not None
        assert t.subject == "geography"
        assert t.unit == "weather"

    def test_select_template_unit_not_found(self, session, kid):
        """ValueError when unit has no templates."""
        with pytest.raises(ValueError, match="No templates for"):
            _select_template(
                session, kid,
                skill=None,
                chapter=None,
                subject="nonexistent",
                unit="fake_unit",
                template_id=None,
            )


# ---------------------------------------------------------------------------
# End-to-end question generation — unit quest
# ---------------------------------------------------------------------------

class TestUnitQuestGeneration:
    def test_generate_question_for_unit(self, session, kid):
        """generate_question works with subject+unit parameters."""
        templates = get_templates_by_unit("geography", "weather")
        if not templates:
            pytest.skip("No geography weather templates loaded")

        instance = generate_question(
            session, kid,
            subject="geography",
            unit="weather",
        )
        assert instance.id is not None
        assert instance.prompt_rendered
        # Template should be from the requested unit
        assert any(t.id == instance.template_id for t in templates)

    def test_generate_question_skill_overrides_unit(self, session, kid):
        """When skill is given, it takes priority over unit."""
        templates = get_templates_by_unit("geography", "weather")
        if not templates:
            pytest.skip("No geography weather templates loaded")

        skill_code = templates[0].skill
        instance = generate_question(
            session, kid,
            skill=skill_code,
            subject="geography",
            unit="weather",
        )
        assert instance.skill == skill_code

    def test_unit_quest_multiple_skills(self, session, kid):
        """Unit quest generates questions across multiple skills in the unit."""
        templates = get_templates_by_unit("geography", "weather")
        if not templates:
            pytest.skip("No geography weather templates loaded")

        unique_skills = {t.skill for t in templates}
        if len(unique_skills) < 2:
            pytest.skip("Need at least 2 skills in unit for this test")

        # Generate several questions; should eventually hit multiple skills
        skills_seen = set()
        for _ in range(20):
            instance = generate_question(
                session, kid,
                subject="geography",
                unit="weather",
            )
            skills_seen.add(instance.skill)

        assert len(skills_seen) >= 2, f"Expected multiple skills, got {skills_seen}"
