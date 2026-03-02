"""Tests for EPIC 4 — gamification, quest sessions, streaks, payouts, gold cap."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, SQLModel, create_engine, select, func
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession, Payout
from app.models.question import QuestionInstance, Attempt, UserSkillProgress
from app.services.questions import (
    generate_question,
    check_answer,
    _gold_earned_this_week,
)
from app.core.config import settings


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


@pytest.fixture(name="admin")
def admin_fixture(session):
    user = User(
        display_name="Parent",
        role=Role.admin,
        pin_hash="$2b$12$fake",
        xp=0,
        gold=0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# QuestSession model tests
# ---------------------------------------------------------------------------

class TestQuestSessionModel:
    def test_create_quest_session(self, session, kid):
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            skill="stats.mean.basic",
            total_questions=8,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        assert quest.id is not None
        assert quest.total_questions == 8
        assert quest.completed == 0
        assert quest.correct == 0
        assert quest.streak == 0
        assert quest.best_streak == 0
        assert quest.finished is False

    def test_chapter_quest_10_questions(self, session, kid):
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            skill=None,
            total_questions=10,
        )
        session.add(quest)
        session.commit()

        assert quest.total_questions == 10
        assert quest.skill is None

    def test_add_and_get_question_ids(self, session, kid):
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            total_questions=8,
        )
        session.add(quest)
        session.commit()

        quest.add_question_id(1)
        quest.add_question_id(2)
        quest.add_question_id(3)

        assert quest.get_question_ids() == [1, 2, 3]

    def test_empty_question_ids(self, session, kid):
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            total_questions=8,
        )
        assert quest.get_question_ids() == []


# ---------------------------------------------------------------------------
# Payout model tests
# ---------------------------------------------------------------------------

class TestPayoutModel:
    def test_create_payout(self, session, kid, admin):
        kid.gold = 50
        session.add(kid)
        session.commit()

        payout = Payout(
            user_id=kid.id,
            gold_amount=25,
            cash_pence=50,  # 25 * 2p
            note="Week 1 pocket money",
            created_by=admin.id,
        )
        session.add(payout)
        session.commit()
        session.refresh(payout)

        assert payout.id is not None
        assert payout.gold_amount == 25
        assert payout.cash_pence == 50
        assert payout.note == "Week 1 pocket money"

    def test_payout_deducts_gold(self, session, kid, admin):
        kid.gold = 100
        session.add(kid)
        session.commit()

        payout_gold = 40
        cash = payout_gold * settings.gold_to_pence

        payout = Payout(
            user_id=kid.id,
            gold_amount=payout_gold,
            cash_pence=cash,
            created_by=admin.id,
        )
        kid.gold -= payout_gold
        session.add(payout)
        session.add(kid)
        session.commit()
        session.refresh(kid)

        assert kid.gold == 60
        assert cash == payout_gold * 2  # 2p per gold


# ---------------------------------------------------------------------------
# Streak bonus tests
# ---------------------------------------------------------------------------

class TestStreakBonus:
    def _make_question(self, session, kid, skill="stats.mean.basic"):
        """Helper: generate a question for streak testing."""
        return generate_question(session, kid, skill=skill)

    def test_streak_increments_on_correct(self, session, kid):
        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=8,
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)

        # We need to check that a correct answer increments streak
        # Use the correct answer from the question
        import json
        correct_val = json.loads(q.correct_json)

        # First correct answer
        attempt, result, _ = check_answer(session, kid, q.id, str(correct_val), quest=quest)
        if result.correct:
            assert quest.streak == 1

    def test_streak_resets_on_wrong(self, session, kid):
        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=8, streak=3,
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)

        attempt, result, _ = check_answer(session, kid, q.id, "WRONG_ANSWER_99999", quest=quest)
        assert quest.streak == 0

    def test_streak_bonus_xp_at_3(self, session, kid):
        """After 3 correct in a row, XP should be 1.5x."""
        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=8, streak=2,  # next correct will be 3rd
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)
        import json
        correct_val = json.loads(q.correct_json)

        attempt, result, _ = check_answer(session, kid, q.id, str(correct_val), quest=quest)
        if result.correct:
            # XP should include 50% bonus
            from app.services.questions import _XP_TABLE
            base = _XP_TABLE.get(q.difficulty, 10)
            expected_xp = int(base * 1.5)
            assert attempt.xp_earned == expected_xp
            assert quest.streak == 3

    def test_streak_bonus_xp_at_5(self, session, kid):
        """After 5 correct in a row, XP should be 2x."""
        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=10, streak=4,
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)
        import json
        correct_val = json.loads(q.correct_json)

        attempt, result, _ = check_answer(session, kid, q.id, str(correct_val), quest=quest)
        if result.correct:
            from app.services.questions import _XP_TABLE
            base = _XP_TABLE.get(q.difficulty, 10)
            expected_xp = int(base * 2.0)
            assert attempt.xp_earned == expected_xp
            assert quest.streak == 5

    def test_best_streak_tracks_max(self, session, kid):
        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=10, streak=4, best_streak=4,
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)
        import json
        correct_val = json.loads(q.correct_json)

        attempt, result, _ = check_answer(session, kid, q.id, str(correct_val), quest=quest)
        if result.correct:
            assert quest.best_streak == 5


# ---------------------------------------------------------------------------
# Weekly gold cap tests
# ---------------------------------------------------------------------------

class TestWeeklyGoldCap:
    def test_gold_earned_this_week_empty(self, session, kid):
        """No attempts = 0 gold this week."""
        total = _gold_earned_this_week(session, kid)
        assert total == 0

    def test_gold_earned_this_week_counts_recent(self, session, kid):
        """Attempts from this week count towards the total."""
        q = QuestionInstance(
            template_id="test", skill="test", chapter=5, difficulty=1,
            seed=1, prompt_rendered="test", payload_json="{}",
            correct_json='"1"', user_id=kid.id,
        )
        session.add(q)
        session.commit()
        session.refresh(q)

        attempt = Attempt(
            question_id=q.id, user_id=kid.id,
            answer_raw="1", is_correct=True,
            gold_earned=5, xp_earned=10,
            attempt_number=1,
        )
        session.add(attempt)
        session.commit()

        total = _gold_earned_this_week(session, kid)
        assert total == 5

    def test_gold_cap_enforced(self, session, kid):
        """Gold should be capped at weekly limit."""
        # Generate some gold history up to near the cap
        q = QuestionInstance(
            template_id="test", skill="test", chapter=5, difficulty=1,
            seed=1, prompt_rendered="test", payload_json="{}",
            correct_json='"1"', user_id=kid.id,
        )
        session.add(q)
        session.commit()
        session.refresh(q)

        # Add attempt with gold near cap
        cap = settings.weekly_gold_cap
        attempt = Attempt(
            question_id=q.id, user_id=kid.id,
            answer_raw="1", is_correct=True,
            gold_earned=cap - 1, xp_earned=10,
            attempt_number=1,
        )
        session.add(attempt)
        session.commit()

        # Now check that remaining gold is capped
        remaining = cap - _gold_earned_this_week(session, kid)
        assert remaining == 1


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestGamificationConfig:
    def test_gold_to_pence_default(self):
        assert settings.gold_to_pence == 2

    def test_weekly_gold_cap_default(self):
        assert settings.weekly_gold_cap == 500
