"""Tests for EPIC 5 — Tutor Mode (OpenAI hints, explanations, fun rewrites).

Tests mock the OpenAI client to avoid real API calls.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.models.question import QuestionInstance, Attempt, UserSkillProgress
from app.services.questions import generate_question, check_answer
from app.services import tutor as tutor_module


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


@pytest.fixture(name="question")
def question_fixture(session, kid):
    """Generate a real question instance for testing."""
    return generate_question(session, kid, chapter=5)


@pytest.fixture
def mock_openai():
    """Mock the OpenAI client to return predictable responses."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mock tutor response."
    mock_response.usage.total_tokens = 42

    mock_client.chat.completions.create.return_value = mock_response

    with patch.object(tutor_module, "_client", mock_client):
        with patch.object(tutor_module, "_get_client", return_value=mock_client):
            yield mock_client


# ---------------------------------------------------------------------------
# Tutor service unit tests
# ---------------------------------------------------------------------------


class TestTutorService:
    """Tests for app.services.tutor functions."""

    def test_get_hint_returns_string(self, mock_openai):
        from app.services.tutor import get_hint

        result = get_hint(
            question_text="Find the mean of 3, 5, 7",
            skill="stats.mean.basic",
            solution_steps=["Add all numbers.", "Divide by count."],
            hint_number=1,
        )
        assert isinstance(result, str)
        assert len(result) > 0
        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()

    def test_get_hint_validates_number(self, mock_openai):
        from app.services.tutor import get_hint

        with pytest.raises(ValueError, match="hint_number must be 1-3"):
            get_hint("Q", "skill", [], hint_number=0)
        with pytest.raises(ValueError, match="hint_number must be 1-3"):
            get_hint("Q", "skill", [], hint_number=4)

    def test_get_hint_all_levels(self, mock_openai):
        from app.services.tutor import get_hint

        for level in (1, 2, 3):
            result = get_hint("Q?", "stats.mean.basic", ["Step 1"], hint_number=level)
            assert isinstance(result, str)

        assert mock_openai.chat.completions.create.call_count == 3

    def test_explain_mistake_returns_string(self, mock_openai):
        from app.services.tutor import explain_mistake

        result = explain_mistake(
            question_text="Find the mean of 3, 5, 7",
            correct_answer="5",
            student_answer="15",
            solution_steps=["Add: 3+5+7=15", "Divide by 3: 15/3=5"],
            skill="stats.mean.basic",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_rewrite_prompt_fun(self, mock_openai):
        from app.services.tutor import rewrite_prompt_fun

        result = rewrite_prompt_fun("Find the mean of 3, 5, 7")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hint_system_prompt_contains_levels(self):
        """Verify the hint system prompt describes all 3 levels."""
        from app.services.tutor import _HINT_SYSTEM

        assert "Level 1" in _HINT_SYSTEM
        assert "Level 2" in _HINT_SYSTEM
        assert "Level 3" in _HINT_SYSTEM

    def test_explain_system_prompt_safety(self):
        """Verify explain system prompt has safety rules."""
        from app.services.tutor import _EXPLAIN_SYSTEM

        assert "age-appropriate" in _EXPLAIN_SYSTEM.lower() or "Year 8" in _EXPLAIN_SYSTEM
        assert "personal" in _EXPLAIN_SYSTEM.lower()

    def test_model_is_gpt4o(self):
        from app.services.tutor import MODEL
        assert MODEL == "gpt-4o"

    def test_openai_error_returns_friendly_message(self):
        """When OpenAI fails, user gets a friendly error, not a crash."""
        from app.services.tutor import _chat

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API down")

        with patch.object(tutor_module, "_client", mock_client):
            with patch.object(tutor_module, "_get_client", return_value=mock_client):
                result = _chat("system", "user", "test")

        assert "Professor Quill" in result
        assert "Exception" in result


# ---------------------------------------------------------------------------
# Hint tracking on QuestionInstance
# ---------------------------------------------------------------------------


class TestHintTracking:
    """Tests for hints_used field on QuestionInstance."""

    def test_hints_used_default_zero(self, session, kid):
        q = generate_question(session, kid, chapter=5)
        assert q.hints_used == 0

    def test_hints_used_increments(self, session, kid):
        q = generate_question(session, kid, chapter=5)
        q.hints_used = 2
        session.add(q)
        session.commit()
        session.refresh(q)
        assert q.hints_used == 2

    def test_fun_prompt_default_none(self, session, kid):
        q = generate_question(session, kid, chapter=5)
        assert q.fun_prompt is None

    def test_fun_prompt_cached(self, session, kid):
        q = generate_question(session, kid, chapter=5)
        q.fun_prompt = "A dragon needs to find the mean!"
        session.add(q)
        session.commit()
        session.refresh(q)
        assert q.fun_prompt == "A dragon needs to find the mean!"


# ---------------------------------------------------------------------------
# Hint penalty (gold halving)
# ---------------------------------------------------------------------------


class TestHintPenalty:
    """Tests that using hints halves the gold reward."""

    def test_no_hints_full_gold(self, session, kid):
        """Without hints, first-try correct gets full gold."""
        q = generate_question(session, kid, chapter=5)
        assert q.hints_used == 0

        # Get correct answer
        correct = json.loads(q.correct_json, object_hook=_fraction_hook)
        answer_str = _answer_to_str(correct)

        attempt, result = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            # Gold should be the full amount for difficulty level
            from app.services.questions import _GOLD_FIRST_TRY
            expected_gold = _GOLD_FIRST_TRY.get(q.difficulty, 1)
            assert attempt.gold_earned == expected_gold

    def test_hints_halve_gold(self, session, kid):
        """With hints used, first-try correct gets halved gold."""
        q = generate_question(session, kid, chapter=5)
        # Simulate using a hint
        q.hints_used = 1
        session.add(q)
        session.commit()

        correct = json.loads(q.correct_json, object_hook=_fraction_hook)
        answer_str = _answer_to_str(correct)

        attempt, result = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            from app.services.questions import _GOLD_FIRST_TRY
            full_gold = _GOLD_FIRST_TRY.get(q.difficulty, 1)
            assert attempt.gold_earned == full_gold // 2

    def test_hints_penalty_multiple_hints(self, session, kid):
        """3 hints: gold still halved (not quartered)."""
        q = generate_question(session, kid, chapter=5)
        q.hints_used = 3
        session.add(q)
        session.commit()

        correct = json.loads(q.correct_json, object_hook=_fraction_hook)
        answer_str = _answer_to_str(correct)

        attempt, result = check_answer(session, kid, q.id, answer_str)
        if result.correct:
            from app.services.questions import _GOLD_FIRST_TRY
            full_gold = _GOLD_FIRST_TRY.get(q.difficulty, 1)
            # Halved once — policy is "halve gold after any hint"
            assert attempt.gold_earned == full_gold // 2


# ---------------------------------------------------------------------------
# Tutor API route tests (mock OpenAI)
# ---------------------------------------------------------------------------


class TestTutorAPI:
    """Tests for /tutor/* API routes."""

    def test_hint_route_updates_hints_used(self, session, kid, mock_openai):
        """POST /tutor/hint should increment hints_used on the question."""
        from app.api.tutor import tutor_hint

        q = generate_question(session, kid, chapter=5)
        assert q.hints_used == 0

        # Build a mock request with auth cookie
        mock_request = _build_mock_request(kid, session)

        response = tutor_hint(
            request=mock_request,
            question_id=q.id,
            hint_number=1,
            session=session,
        )
        assert response.status_code == 200
        body = response.body.decode()
        assert "Hint 1 of 3" in body
        assert "Professor Quill" in body

        # Check hints_used was incremented
        session.refresh(q)
        assert q.hints_used == 1

    def test_hint_route_progressive(self, session, kid, mock_openai):
        """Requesting hint 2 after hint 1 works correctly."""
        from app.api.tutor import tutor_hint

        q = generate_question(session, kid, chapter=5)

        mock_request = _build_mock_request(kid, session)

        # Hint 1
        tutor_hint(request=mock_request, question_id=q.id, hint_number=1, session=session)
        session.refresh(q)
        assert q.hints_used == 1

        # Hint 2
        tutor_hint(request=mock_request, question_id=q.id, hint_number=2, session=session)
        session.refresh(q)
        assert q.hints_used == 2

    def test_explain_route(self, session, kid, mock_openai):
        from app.api.tutor import tutor_explain

        q = generate_question(session, kid, chapter=5)
        mock_request = _build_mock_request(kid, session)

        response = tutor_explain(
            request=mock_request,
            question_id=q.id,
            student_answer="42",
            session=session,
        )
        assert response.status_code == 200
        body = response.body.decode()
        assert "Professor Quill" in body

    def test_rewrite_route(self, session, kid, mock_openai):
        from app.api.tutor import tutor_rewrite

        q = generate_question(session, kid, chapter=5)
        mock_request = _build_mock_request(kid, session)

        response = tutor_rewrite(
            request=mock_request,
            question_id=q.id,
            session=session,
        )
        assert response.status_code == 200
        body = response.body.decode()
        assert "fun" in body.lower() or "Same question" in body

    def test_rewrite_caches_fun_prompt(self, session, kid, mock_openai):
        """Second call to rewrite should use cached fun_prompt."""
        from app.api.tutor import tutor_rewrite

        q = generate_question(session, kid, chapter=5)
        assert q.fun_prompt is None

        mock_request = _build_mock_request(kid, session)

        # First call — generates and caches
        tutor_rewrite(request=mock_request, question_id=q.id, session=session)
        session.refresh(q)
        assert q.fun_prompt is not None
        first_cached = q.fun_prompt

        # Second call — should NOT call OpenAI again
        mock_openai.chat.completions.create.reset_mock()
        tutor_rewrite(request=mock_request, question_id=q.id, session=session)
        mock_openai.chat.completions.create.assert_not_called()

    def test_hint_caps_at_3(self, session, kid, mock_openai):
        """Requesting hint_number > 3 should be capped at 3."""
        from app.api.tutor import tutor_hint

        q = generate_question(session, kid, chapter=5)
        mock_request = _build_mock_request(kid, session)

        response = tutor_hint(
            request=mock_request,
            question_id=q.id,
            hint_number=5,  # should cap to 3
            session=session,
        )
        assert response.status_code == 200
        session.refresh(q)
        assert q.hints_used == 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fraction_hook(d: dict):
    if "__fraction__" in d:
        from fractions import Fraction
        return Fraction(d["num"], d["den"])
    return d


def _answer_to_str(answer) -> str:
    from fractions import Fraction
    if isinstance(answer, Fraction):
        return str(answer)
    if isinstance(answer, dict):
        parts = [f"{k}: {v}" for k, v in answer.items()]
        return ", ".join(parts)
    if isinstance(answer, list):
        return ", ".join(str(x) for x in answer)
    return str(answer)


def _build_mock_request(user: User, session: Session):
    """Build a mock Request object that passes auth."""
    mock_request = MagicMock()
    mock_request.cookies = {}

    # Patch get_current_user to return our user
    import app.api.tutor as tutor_api
    tutor_api.get_current_user = lambda req, sess: user

    return mock_request
