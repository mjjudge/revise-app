"""Tests for EPIC 10 — per-subject progress tracking."""

import pytest
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession
from app.models.question import QuestionInstance, SubjectProgress
from app.services.questions import (
    check_answer,
    generate_question,
    get_subject_progress,
    get_all_subject_progress,
    _update_subject_progress,
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


# ---------------------------------------------------------------------------
# SubjectProgress model tests
# ---------------------------------------------------------------------------

class TestSubjectProgressModel:
    def test_create_subject_progress(self, session, kid):
        """SubjectProgress can be created with defaults."""
        sp = SubjectProgress(user_id=kid.id, subject="maths")
        session.add(sp)
        session.commit()
        session.refresh(sp)

        assert sp.id is not None
        assert sp.subject == "maths"
        assert sp.xp_earned == 0
        assert sp.gold_earned == 0
        assert sp.quests_completed == 0
        assert sp.questions_answered == 0
        assert sp.questions_correct == 0
        assert sp.best_streak == 0
        assert sp.last_played is None

    def test_separate_rows_per_subject(self, session, kid):
        """Different subjects get separate rows."""
        sp1 = SubjectProgress(user_id=kid.id, subject="maths", xp_earned=100)
        sp2 = SubjectProgress(user_id=kid.id, subject="geography", xp_earned=50)
        session.add(sp1)
        session.add(sp2)
        session.commit()

        rows = session.exec(
            select(SubjectProgress).where(SubjectProgress.user_id == kid.id)
        ).all()
        assert len(rows) == 2
        subjects = {r.subject for r in rows}
        assert subjects == {"maths", "geography"}


# ---------------------------------------------------------------------------
# _update_subject_progress helper
# ---------------------------------------------------------------------------

class TestUpdateSubjectProgress:
    def test_creates_when_missing(self, session, kid):
        """First call creates a new SubjectProgress row."""
        _update_subject_progress(
            session, kid, "maths",
            xp_earned=10, gold_earned=2, correct=True,
            quest_finished=False, streak=1,
        )
        session.commit()

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp is not None
        assert sp.xp_earned == 10
        assert sp.gold_earned == 2
        assert sp.questions_answered == 1
        assert sp.questions_correct == 1
        assert sp.best_streak == 1

    def test_increments_on_subsequent_calls(self, session, kid):
        """Repeated calls accumulate stats."""
        for i in range(3):
            _update_subject_progress(
                session, kid, "maths",
                xp_earned=5, gold_earned=1, correct=True,
                quest_finished=False, streak=i + 1,
            )
        session.commit()

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp.xp_earned == 15
        assert sp.gold_earned == 3
        assert sp.questions_answered == 3
        assert sp.questions_correct == 3
        assert sp.best_streak == 3

    def test_incorrect_does_not_increment_correct(self, session, kid):
        """Wrong answers still count as answered but not correct."""
        _update_subject_progress(
            session, kid, "maths",
            xp_earned=0, gold_earned=0, correct=False,
            quest_finished=False, streak=0,
        )
        session.commit()

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp.questions_answered == 1
        assert sp.questions_correct == 0

    def test_quest_finished_increments_quests_completed(self, session, kid):
        """When quest_finished=True, quests_completed goes up."""
        _update_subject_progress(
            session, kid, "geography",
            xp_earned=10, gold_earned=2, correct=True,
            quest_finished=True, streak=5,
        )
        session.commit()

        sp = get_subject_progress(session, kid.id, "geography")
        assert sp.quests_completed == 1

    def test_best_streak_only_increases(self, session, kid):
        """best_streak only updates when new streak is higher."""
        _update_subject_progress(
            session, kid, "maths",
            xp_earned=5, gold_earned=1, correct=True,
            quest_finished=False, streak=5,
        )
        _update_subject_progress(
            session, kid, "maths",
            xp_earned=5, gold_earned=1, correct=True,
            quest_finished=False, streak=2,
        )
        session.commit()

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp.best_streak == 5  # not overwritten by 2

    def test_sets_last_played(self, session, kid):
        """last_played is set on each update."""
        _update_subject_progress(
            session, kid, "maths",
            xp_earned=5, gold_earned=1, correct=True,
            quest_finished=False, streak=1,
        )
        session.commit()

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp.last_played is not None


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

class TestSubjectProgressQueries:
    def test_get_subject_progress_returns_none(self, session, kid):
        """Returns None when no progress exists."""
        assert get_subject_progress(session, kid.id, "maths") is None

    def test_get_subject_progress_returns_row(self, session, kid):
        """Returns the SubjectProgress when it exists."""
        sp = SubjectProgress(user_id=kid.id, subject="maths", xp_earned=42)
        session.add(sp)
        session.commit()

        result = get_subject_progress(session, kid.id, "maths")
        assert result is not None
        assert result.xp_earned == 42

    def test_get_all_subject_progress_empty(self, session, kid):
        """Returns empty dict when no progress."""
        result = get_all_subject_progress(session, kid.id)
        assert result == {}

    def test_get_all_subject_progress_multiple(self, session, kid):
        """Returns dict keyed by subject."""
        session.add(SubjectProgress(user_id=kid.id, subject="maths", xp_earned=100))
        session.add(SubjectProgress(user_id=kid.id, subject="geography", xp_earned=50))
        session.commit()

        result = get_all_subject_progress(session, kid.id)
        assert len(result) == 2
        assert "maths" in result
        assert "geography" in result
        assert result["maths"].xp_earned == 100
        assert result["geography"].xp_earned == 50


# ---------------------------------------------------------------------------
# Integration: check_answer updates SubjectProgress
# ---------------------------------------------------------------------------

class TestCheckAnswerSubjectProgress:
    def test_maths_question_tracks_maths_subject(self, session, kid):
        """Answering a maths question updates maths SubjectProgress."""
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            subject="maths",
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        q = generate_question(session, kid, chapter=5)
        attempt, result = check_answer(session, kid, q.id, "0", quest=quest)

        sp = get_subject_progress(session, kid.id, "maths")
        assert sp is not None
        assert sp.questions_answered >= 1

    def test_geography_question_tracks_geography_subject(self, session, kid):
        """Answering a geography question updates geography SubjectProgress."""
        quest = QuestSession(
            user_id=kid.id,
            subject="geography",
            unit="maps",
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        q = generate_question(session, kid, subject="geography", unit="maps")
        attempt, result = check_answer(session, kid, q.id, "0", quest=quest)

        sp = get_subject_progress(session, kid.id, "geography")
        assert sp is not None
        assert sp.questions_answered >= 1

    def test_correct_answer_earns_xp_in_subject(self, session, kid):
        """Correct first-try answer adds XP to SubjectProgress."""
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            subject="maths",
            total_questions=10,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        q = generate_question(session, kid, chapter=5)
        # Get the correct answer
        correct_ans = q.correct
        if isinstance(correct_ans, list):
            correct_ans = correct_ans[0]

        attempt, result = check_answer(
            session, kid, q.id, str(correct_ans), quest=quest,
        )

        if result.correct:
            sp = get_subject_progress(session, kid.id, "maths")
            assert sp.xp_earned > 0
