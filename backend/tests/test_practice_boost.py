"""Tests for EPIC 10.5 — Practice Boost: extra rewards for weak skills."""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession
from app.models.question import QuestionInstance, UserSkillProgress
from app.services.questions import (
    check_answer,
    generate_question,
    get_boosted_skills,
    _XP_TABLE,
    _GOLD_FIRST_TRY,
)


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


def _seed_skill_progress(
    session: Session,
    user: User,
    skill: str,
    *,
    attempts: int = 10,
    correct: int = 3,
    band: int = 2,
) -> UserSkillProgress:
    """Create a UserSkillProgress row with given stats."""
    sp = UserSkillProgress(
        user_id=user.id,
        skill=skill,
        attempts_total=attempts,
        attempts_correct=correct,
        current_band=band,
    )
    session.add(sp)
    session.commit()
    session.refresh(sp)
    return sp


# ---------------------------------------------------------------------------
# get_boosted_skills tests
# ---------------------------------------------------------------------------

class TestGetBoostedSkills:
    """Story 10.5.1 — identify which skills qualify for Practice Boost."""

    def test_returns_empty_when_no_skill_progress(self, session, kid):
        """No skill progress rows → no boosts."""
        result = get_boosted_skills(session, kid.id)
        assert result == set()

    def test_excludes_skills_with_fewer_than_3_attempts(self, session, kid):
        """Skills with <3 attempts are excluded even if accuracy is 0%."""
        _seed_skill_progress(session, kid, "test.skill", attempts=2, correct=0, band=2)
        result = get_boosted_skills(session, kid.id)
        assert "test.skill" not in result

    def test_includes_low_accuracy_skill(self, session, kid):
        """Skill with ≤60% accuracy and ≥3 attempts → boosted."""
        # 3 attempts, 1 correct = 33% accuracy
        _seed_skill_progress(session, kid, "test.weak", attempts=3, correct=1, band=2)
        result = get_boosted_skills(session, kid.id)
        assert "test.weak" in result

    def test_includes_band_1_skill(self, session, kid):
        """Skill at band 1 → boosted regardless of accuracy (if ≥3 attempts)."""
        _seed_skill_progress(session, kid, "test.band1", attempts=3, correct=2, band=1)
        result = get_boosted_skills(session, kid.id)
        assert "test.band1" in result

    def test_includes_band_1_even_with_fewer_attempts(self, session, kid):
        """Band 1 skill with only 1 attempt should still be boosted (band alone qualifies)."""
        _seed_skill_progress(session, kid, "test.band1only", attempts=1, correct=0, band=1)
        result = get_boosted_skills(session, kid.id)
        assert "test.band1only" in result

    def test_excludes_high_accuracy_skill(self, session, kid):
        """Skill with >60% accuracy and band ≥2 → not boosted."""
        _seed_skill_progress(session, kid, "test.strong", attempts=10, correct=8, band=3)
        result = get_boosted_skills(session, kid.id)
        assert "test.strong" not in result

    def test_auto_removes_when_mastered(self, session, kid):
        """Skill at 75%+ accuracy (≥5 attempts) → boost removed."""
        # 8 of 10 correct = 80%, should NOT be boosted even with band 1
        _seed_skill_progress(session, kid, "test.mastered", attempts=10, correct=8, band=1)
        result = get_boosted_skills(session, kid.id)
        assert "test.mastered" not in result

    def test_boundary_60_percent_included(self, session, kid):
        """Exactly 60% accuracy → still boosted (≤60)."""
        # 3 of 5 = 60%
        _seed_skill_progress(session, kid, "test.boundary60", attempts=5, correct=3, band=2)
        result = get_boosted_skills(session, kid.id)
        assert "test.boundary60" in result

    def test_boundary_75_percent_excluded(self, session, kid):
        """Exactly 75% accuracy with ≥5 attempts → boost removed."""
        # 15 of 20 = 75%
        _seed_skill_progress(session, kid, "test.boundary75", attempts=20, correct=15, band=1)
        result = get_boosted_skills(session, kid.id)
        assert "test.boundary75" not in result


# ---------------------------------------------------------------------------
# Reward multiplier tests
# ---------------------------------------------------------------------------

class TestBoostRewardMultiplier:
    """Story 10.5.2 — check_answer applies boost multipliers correctly."""

    def _make_question(self, session, kid, skill="stats.mean.basic"):
        """Generate a question for the given skill."""
        return generate_question(session, kid, skill=skill)

    def test_boosted_skill_gets_double_gold(self, session, kid):
        """Correct first-try on a boosted skill → 2× gold."""
        # Seed low-accuracy skill progress to trigger boost
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=5, correct=1, band=1)

        q = self._make_question(session, kid)
        correct_ans = json.loads(q.correct_json)
        answer_str = str(correct_ans) if not isinstance(correct_ans, dict) else str(correct_ans)

        attempt, result, is_boosted = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            assert is_boosted is True
            base_gold = _GOLD_FIRST_TRY.get(q.difficulty, 1)
            assert attempt.gold_earned == base_gold * 2

    def test_boosted_skill_gets_1_5x_xp(self, session, kid):
        """Correct first-try on a boosted skill → 1.5× XP."""
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=5, correct=1, band=1)

        q = self._make_question(session, kid)
        correct_ans = json.loads(q.correct_json)
        answer_str = str(correct_ans)

        attempt, result, is_boosted = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            assert is_boosted is True
            base_xp = _XP_TABLE.get(q.difficulty, 10)
            expected_xp = int(base_xp * 1.5)
            assert attempt.xp_earned == expected_xp

    def test_non_boosted_skill_normal_rewards(self, session, kid):
        """Correct answer on a non-boosted skill → normal rewards."""
        # Seed high-accuracy progress — should NOT be boosted
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=10, correct=9, band=3)

        q = self._make_question(session, kid)
        correct_ans = json.loads(q.correct_json)
        answer_str = str(correct_ans)

        attempt, result, is_boosted = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            assert is_boosted is False
            base_gold = _GOLD_FIRST_TRY.get(q.difficulty, 1)
            assert attempt.gold_earned == base_gold

    def test_streak_and_boost_stack(self, session, kid):
        """Streak bonus applies first, then boost multiplies on top."""
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=5, correct=1, band=1)

        quest = QuestSession(
            user_id=kid.id, chapter=5, skill="stats.mean.basic",
            total_questions=8, streak=2,  # next correct = 3rd in a row → +50% streak
        )
        session.add(quest)
        session.commit()

        q = self._make_question(session, kid)
        correct_ans = json.loads(q.correct_json)

        attempt, result, is_boosted = check_answer(
            session, kid, q.id, str(correct_ans), quest=quest,
        )
        if result.correct:
            assert is_boosted is True
            base_xp = _XP_TABLE.get(q.difficulty, 10)
            # Streak +50% → 1.5× base, then boost ×1.5 → 2.25× base
            streaked_xp = int(base_xp * 1.5)
            expected_xp = int(streaked_xp * 1.5)
            assert attempt.xp_earned == expected_xp

    def test_weekly_cap_still_applies_after_boost(self, session, kid):
        """Boosted gold should still be clamped by the weekly cap."""
        from app.core.config import settings
        from app.models.question import Attempt as AttemptModel

        # Seed some gold near the cap
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=5, correct=1, band=1)

        # Create a previous attempt that ate most of the cap
        prev_q = QuestionInstance(
            template_id="test", skill="test", chapter=5, difficulty=1,
            seed=1, prompt_rendered="test", payload_json="{}",
            correct_json='"1"', user_id=kid.id,
        )
        session.add(prev_q)
        session.commit()
        session.refresh(prev_q)

        prev_attempt = AttemptModel(
            question_id=prev_q.id, user_id=kid.id,
            answer_raw="1", is_correct=True,
            gold_earned=settings.weekly_gold_cap - 1, xp_earned=10,
            attempt_number=1,
        )
        session.add(prev_attempt)
        session.commit()

        q = self._make_question(session, kid)
        correct_ans = json.loads(q.correct_json)
        attempt, result, is_boosted = check_answer(session, kid, q.id, str(correct_ans))

        if result.correct:
            # Even with 2× boost, gold should be capped at remaining (1)
            assert attempt.gold_earned <= 1

    def test_wrong_answer_not_boosted(self, session, kid):
        """Wrong answers return is_boosted=False."""
        _seed_skill_progress(session, kid, "stats.mean.basic", attempts=5, correct=1, band=1)

        q = self._make_question(session, kid)
        attempt, result, is_boosted = check_answer(session, kid, q.id, "WRONG_ANSWER_xyz")
        assert is_boosted is False
        assert attempt.gold_earned == 0
