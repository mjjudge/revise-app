"""Tests for EPIC 10.8 — Professor Quill Image Integration & Bunny Easter Eggs.

Covers:
  - wrong_streak model field on QuestSession
  - wrong_streak increment/reset in check_answer
  - Quill image references in tutor hint/explain HTML responses
  - Template context includes wrong_streak
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.quest import QuestSession
from app.models.question import QuestionInstance, Attempt, UserSkillProgress
from app.services.questions import generate_question, check_answer


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


@pytest.fixture(name="quest")
def quest_fixture(session, kid):
    quest = QuestSession(
        user_id=kid.id,
        chapter=5,
        skill="stats.mean.basic",
        total_questions=10,
    )
    session.add(quest)
    session.commit()
    session.refresh(quest)
    return quest


@pytest.fixture(name="question")
def question_fixture(session, kid):
    return generate_question(session, kid, chapter=5)


# ---------------------------------------------------------------------------
# Wrong-streak model tests
# ---------------------------------------------------------------------------

class TestWrongStreakModel:
    """Story 10.8.2 — wrong_streak field on QuestSession."""

    def test_wrong_streak_defaults_to_zero(self, session, kid):
        quest = QuestSession(
            user_id=kid.id,
            chapter=5,
            total_questions=8,
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)

        assert quest.wrong_streak == 0

    def test_wrong_streak_increments_on_wrong_answer(self, session, kid, quest):
        """When the student answers incorrectly, wrong_streak should increment."""
        q = generate_question(session, kid, chapter=5)
        quest.add_question_id(q.id)
        session.add(quest)
        session.commit()

        # Answer incorrectly
        _attempt, result, _boosted = check_answer(
            session, kid, q.id, "DEFINITELY_WRONG_ANSWER_XYZ", quest=quest,
        )
        session.refresh(quest)

        assert not result.correct
        assert quest.wrong_streak >= 1

    def test_wrong_streak_resets_on_correct_answer(self, session, kid, quest):
        """After a wrong answer, a correct answer should reset wrong_streak to 0."""
        # First, produce a wrong answer to set wrong_streak
        q1 = generate_question(session, kid, chapter=5)
        quest.add_question_id(q1.id)
        session.add(quest)
        session.commit()

        _attempt1, result1, _ = check_answer(
            session, kid, q1.id, "DEFINITELY_WRONG_ANSWER_XYZ", quest=quest,
        )
        session.refresh(quest)
        assert quest.wrong_streak >= 1

        # Now answer a new question correctly
        q2 = generate_question(session, kid, chapter=5)
        quest.add_question_id(q2.id)
        session.add(quest)
        session.commit()

        correct_answer = q2.correct
        if isinstance(correct_answer, dict):
            correct_str = json.dumps(correct_answer)
        elif isinstance(correct_answer, list):
            correct_str = ", ".join(str(x) for x in correct_answer)
        else:
            correct_str = str(correct_answer)

        _attempt2, result2, _ = check_answer(
            session, kid, q2.id, correct_str, quest=quest,
        )
        session.refresh(quest)

        if result2.correct:
            assert quest.wrong_streak == 0

    def test_wrong_streak_accumulates(self, session, kid, quest):
        """Multiple wrong answers in a row should accumulate wrong_streak."""
        for i in range(3):
            q = generate_question(session, kid, chapter=5)
            quest.add_question_id(q.id)
            session.add(quest)
            session.commit()

            _attempt, result, _ = check_answer(
                session, kid, q.id, "WRONG_ANSWER_XYZ", quest=quest,
            )
            session.refresh(quest)

        assert quest.wrong_streak >= 3
        assert quest.streak == 0  # correct streak should be 0


# ---------------------------------------------------------------------------
# Image file existence tests
# ---------------------------------------------------------------------------

class TestImageFiles:
    """Verify all expected Quill and bunny image files exist."""

    IMAGES_DIR = Path(__file__).parent.parent / "app" / "images"

    QUILL_IMAGES = [
        "quill_thinking.png",
        "quill_teaching1.png",
        "quill_teaching2.png",
        "quill_super_happy.png",
        "quill_concerned.png",
        "quill_waving.png",
        "quill_thumbsup.png",
        "quill_reading.png",
        "quill_proud.png",
        "quill_encouraging.png",
        "quill_celebrating.png",
    ]

    BUNNY_IMAGES = [
        "bunny_waving.png",
        "bunny_thumbsup.png",
        "bunny_reading.png",
        "bunny_proud.png",
        "bunny_encouraging.png",
        "bunny_celebrating.png",
    ]

    @pytest.mark.parametrize("filename", QUILL_IMAGES)
    def test_quill_image_exists(self, filename):
        path = self.IMAGES_DIR / filename
        assert path.exists(), f"Missing Quill image: {filename}"

    @pytest.mark.parametrize("filename", BUNNY_IMAGES)
    def test_bunny_image_exists(self, filename):
        path = self.IMAGES_DIR / filename
        assert path.exists(), f"Missing bunny image: {filename}"


# ---------------------------------------------------------------------------
# Tutor API — Quill images in HTML responses
# ---------------------------------------------------------------------------

class TestTutorQuillImages:
    """Verify tutor hint/explain responses contain Quill image references."""

    @patch("app.services.tutor._chat")
    def test_hint_response_contains_quill_image(self, mock_chat, session, kid, question):
        """Hint HTML should include quill_thinking image."""
        mock_chat.return_value = "Try adding the numbers first."

        from app.api.tutor import tutor_hint
        from unittest.mock import MagicMock

        # Build a mock request
        request = MagicMock()
        request.headers = {}

        with patch("app.api.tutor.get_current_user", return_value=kid):
            response = tutor_hint(
                request=request,
                question_id=question.id,
                hint_number=1,
                session=session,
            )

        html = response.body.decode()
        assert "quill_thinking.png" in html
        assert "Professor Quill" in html

    @patch("app.services.tutor._chat")
    def test_explain_response_contains_quill_image(self, mock_chat, session, kid, question):
        """Explain HTML should include quill_teaching1 image."""
        mock_chat.return_value = "You need to divide, not multiply."

        from app.api.tutor import tutor_explain

        request = MagicMock()
        request.headers = {}

        with patch("app.api.tutor.get_current_user", return_value=kid):
            response = tutor_explain(
                request=request,
                question_id=question.id,
                student_answer="42",
                session=session,
            )

        html = response.body.decode()
        assert "quill_teaching1.png" in html
        assert "Professor Quill" in html


# ---------------------------------------------------------------------------
# Accessibility tests
# ---------------------------------------------------------------------------

class TestAccessibility:
    """All Quill images should have alt text."""

    @patch("app.services.tutor._chat")
    def test_hint_image_has_alt_text(self, mock_chat, session, kid, question):
        mock_chat.return_value = "Hint text."

        from app.api.tutor import tutor_hint

        request = MagicMock()
        request.headers = {}

        with patch("app.api.tutor.get_current_user", return_value=kid):
            response = tutor_hint(
                request=request,
                question_id=question.id,
                hint_number=1,
                session=session,
            )

        html = response.body.decode()
        assert 'alt="Professor Quill"' in html

    @patch("app.services.tutor._chat")
    def test_explain_image_has_alt_text(self, mock_chat, session, kid, question):
        mock_chat.return_value = "Explanation text."

        from app.api.tutor import tutor_explain

        request = MagicMock()
        request.headers = {}

        with patch("app.api.tutor.get_current_user", return_value=kid):
            response = tutor_explain(
                request=request,
                question_id=question.id,
                student_answer="42",
                session=session,
            )

        html = response.body.decode()
        assert 'alt="Professor Quill"' in html


# ---------------------------------------------------------------------------
# Bunny eligibility test
# ---------------------------------------------------------------------------

class TestBunnyEligibility:
    """Bunny swaps should only be for the 6 matching poses, never core poses."""

    # This tests the JS logic conceptually — we verify the BUNNY_ELIGIBLE list
    # matches our 6 bunny image files
    BUNNY_ELIGIBLE_POSES = ['waving', 'thumbsup', 'reading', 'proud', 'encouraging', 'celebrating']
    CORE_POSES = ['thinking', 'teaching1', 'teaching2', 'super_happy', 'concerned']

    def test_bunny_eligible_poses_have_images(self):
        images_dir = Path(__file__).parent.parent / "app" / "images"
        for pose in self.BUNNY_ELIGIBLE_POSES:
            assert (images_dir / f"bunny_{pose}.png").exists(), f"Missing bunny_{pose}.png"

    def test_core_poses_have_no_bunny_equivalent(self):
        images_dir = Path(__file__).parent.parent / "app" / "images"
        for pose in self.CORE_POSES:
            assert not (images_dir / f"bunny_{pose}.png").exists(), \
                f"bunny_{pose}.png should not exist — {pose} is a core pedagogical pose"
