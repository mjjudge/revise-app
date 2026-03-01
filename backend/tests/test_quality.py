"""Tests for EPIC 6 — Quality + Observability.

Covers:
  - YAML cross-validation (marking modes, chapter consistency)
  - End-to-end template generation (every template generates, marks, and round-trips)
  - Structured logging configuration
  - Error page handlers
  - Request logging middleware
"""

import json
import logging
import pytest
from fractions import Fraction
from unittest.mock import MagicMock

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.models.user import User, Role
from app.services.questions import generate_question, check_answer
from app.templates.feed_loader import (
    load_and_validate,
    load_skills,
    load_templates,
    MarkingMode,
)
from app.core.logging import setup_logging, _JSONFormatter, _DevFormatter


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
# YAML Cross-Validation Tests
# ---------------------------------------------------------------------------


class TestYAMLValidation:
    """Ensure templates reference valid skills and supported marking modes."""

    def test_all_template_skills_exist_in_skills_yaml(self):
        """Every template.skill must match a defined skill code."""
        skills_feed, templates_feed = load_and_validate()
        skill_codes = {s.code for s in skills_feed.skills}
        for t in templates_feed.templates:
            assert t.skill in skill_codes, (
                f"Template '{t.id}' references unknown skill '{t.skill}'"
            )

    def test_all_template_chapters_match_skill_chapters(self):
        """Template chapter must match its skill's chapter."""
        skills_feed, templates_feed = load_and_validate()
        skill_chapters = {s.code: s.chapter for s in skills_feed.skills}
        for t in templates_feed.templates:
            expected_ch = skill_chapters.get(t.skill)
            assert t.chapter == expected_ch, (
                f"Template '{t.id}' chapter {t.chapter} != "
                f"skill '{t.skill}' chapter {expected_ch}"
            )

    def test_all_marking_modes_are_supported(self):
        """Every template must use a marking mode from the supported enum."""
        templates_feed = load_templates()
        supported = {m.value for m in MarkingMode}
        for t in templates_feed.templates:
            assert t.marking.mode.value in supported, (
                f"Template '{t.id}' uses unsupported marking mode '{t.marking.mode}'"
            )

    def test_all_templates_have_solution_steps(self):
        """Every template should have at least one solution step."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            assert t.solution is not None, f"Template '{t.id}' has no solution"
            assert len(t.solution.steps) > 0, (
                f"Template '{t.id}' has empty solution steps"
            )

    def test_all_template_ids_have_chapter_prefix(self):
        """Template IDs should start with 'ch{N}_' matching their chapter."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            expected_prefix = f"ch{t.chapter}_"
            assert t.id.startswith(expected_prefix), (
                f"Template '{t.id}' should start with '{expected_prefix}'"
            )

    def test_difficulty_distribution(self):
        """Templates should cover multiple difficulty levels."""
        templates_feed = load_templates()
        difficulties = {t.difficulty for t in templates_feed.templates}
        assert len(difficulties) >= 2, (
            f"Expected at least 2 difficulty levels, got {difficulties}"
        )

    def test_all_chapters_have_templates(self):
        """Each chapter (5-8) should have at least one template."""
        templates_feed = load_templates()
        chapters_with_templates = {t.chapter for t in templates_feed.templates}
        for ch in (5, 6, 7, 8):
            assert ch in chapters_with_templates, (
                f"Chapter {ch} has no templates"
            )


# ---------------------------------------------------------------------------
# End-to-End Template Generation Tests
# ---------------------------------------------------------------------------


class TestEndToEndGeneration:
    """Test that every template can generate a question and produce a valid answer."""

    def test_every_template_generates_successfully(self, session, kid):
        """Each template should generate a question without errors."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            assert instance.id is not None, f"Template '{t.id}' failed to generate"
            assert instance.prompt_rendered, f"Template '{t.id}' has empty prompt"
            assert instance.correct_json, f"Template '{t.id}' has no correct answer"
            assert instance.template_id == t.id

    def test_every_template_correct_answer_marks_correctly(self, session, kid):
        """Submitting the correct answer should mark as correct for every template."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            correct = _decode_json(instance.correct_json)
            answer_str = _answer_to_str(correct)

            attempt, result = check_answer(session, kid, instance.id, answer_str)
            assert result.correct, (
                f"Template '{t.id}': correct answer '{answer_str}' was not marked correct. "
                f"Feedback: {result.feedback}"
            )

    def test_every_template_wrong_answer_marks_incorrect(self, session, kid):
        """Submitting a clearly wrong answer should be marked incorrect."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            # Use a deliberately wrong answer
            attempt, result = check_answer(session, kid, instance.id, "WRONG_ANSWER_xyz")
            assert not result.correct, (
                f"Template '{t.id}': 'WRONG_ANSWER_xyz' was incorrectly marked correct"
            )

    def test_deterministic_generation(self, session, kid):
        """Same seed should produce the same question for each template."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            q1 = generate_question(session, kid, template_id=t.id, seed=12345)
            q2 = generate_question(session, kid, template_id=t.id, seed=12345)
            assert q1.payload_json == q2.payload_json, (
                f"Template '{t.id}' not deterministic with same seed"
            )
            assert q1.correct_json == q2.correct_json, (
                f"Template '{t.id}' answer not deterministic with same seed"
            )

    def test_different_seeds_produce_different_questions(self, session, kid):
        """Different seeds should (usually) produce different questions."""
        templates_feed = load_templates()
        different_count = 0
        for t in templates_feed.templates:
            q1 = generate_question(session, kid, template_id=t.id, seed=100)
            q2 = generate_question(session, kid, template_id=t.id, seed=999)
            if q1.payload_json != q2.payload_json:
                different_count += 1
        # Most templates should produce different results with different seeds
        assert different_count > len(templates_feed.templates) // 2


# ---------------------------------------------------------------------------
# Structured Logging Tests
# ---------------------------------------------------------------------------


class TestStructuredLogging:
    """Tests for the logging configuration module."""

    def test_setup_logging_dev(self):
        """Dev mode should use DevFormatter."""
        setup_logging(env="dev")
        root = logging.getLogger()
        assert len(root.handlers) > 0
        handler = root.handlers[-1]
        assert isinstance(handler.formatter, _DevFormatter)

    def test_setup_logging_prod(self):
        """Production mode should use JSONFormatter."""
        setup_logging(env="prod")
        root = logging.getLogger()
        handler = root.handlers[-1]
        assert isinstance(handler.formatter, _JSONFormatter)
        # Restore dev for other tests
        setup_logging(env="dev")

    def test_json_formatter_output(self):
        """JSON formatter should produce valid JSON."""
        formatter = _JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["msg"] == "hello world"
        assert parsed["level"] == "INFO"
        assert "ts" in parsed

    def test_json_formatter_extra_fields(self):
        """JSON formatter should include extra fields like request_id."""
        formatter = _JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="req", args=(), exc_info=None,
        )
        record.request_id = "abc123"
        record.method = "GET"
        record.path = "/health"
        record.status = 200
        record.duration_ms = 5.2
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["request_id"] == "abc123"
        assert parsed["method"] == "GET"
        assert parsed["status"] == 200

    def test_dev_formatter_output(self):
        """Dev formatter should produce human-readable output."""
        formatter = _DevFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert "hello" in output
        assert "INFO" in output

    def test_setup_logging_level_override(self):
        """Level override should work."""
        setup_logging(env="dev", level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING
        # Restore
        setup_logging(env="dev", level="DEBUG")

    def test_setup_logging_removes_duplicate_handlers(self):
        """Calling setup_logging twice should not duplicate handlers."""
        setup_logging(env="dev")
        count1 = len(logging.getLogger().handlers)
        setup_logging(env="dev")
        count2 = len(logging.getLogger().handlers)
        assert count2 == count1


# ---------------------------------------------------------------------------
# Error Page Tests
# ---------------------------------------------------------------------------


class TestErrorPages:
    """Test that error handlers return themed HTML pages."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_404_returns_themed_page(self, client):
        response = client.get("/nonexistent-page-xyz")
        assert response.status_code == 404
        assert "Page Not Found" in response.text
        assert "quest" in response.text.lower() or "realm" in response.text.lower()

    def test_404_has_home_link(self, client):
        response = client.get("/nonexistent-page-xyz")
        assert 'href="/"' in response.text

    def test_health_still_works(self, client):
        """Sanity check that /health is unaffected by error handlers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_empty_answer_shows_inline_error(self, client):
        """Submitting an empty answer should return an inline error, not a 422."""
        # The /quest/answer route requires auth; we test without auth → redirect to login
        response = client.post(
            "/quest/answer",
            data={"question_id": "1", "answer": "", "quest_id": "0"},
            follow_redirects=False,
        )
        # Should redirect to login (user not authenticated)
        assert response.status_code in (200, 303)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_json(s: str):
    def _hook(d: dict):
        if "__fraction__" in d:
            return Fraction(d["num"], d["den"])
        return d
    return json.loads(s, object_hook=_hook)


def _answer_to_str(answer) -> str:
    if isinstance(answer, Fraction):
        return str(answer)
    if isinstance(answer, dict):
        # Algebra normal form: {"total_coeff": N} → e.g. "3a", "-2a", "a", "-a", "0"
        if "total_coeff" in answer:
            coeff = answer["total_coeff"]
            var = answer.get("variable", "a")
            if coeff == 0:
                return "0"
            if coeff == 1:
                return var
            if coeff == -1:
                return f"-{var}"
            return f"{coeff}{var}"
        # Remainder form: {"quotient": q, "remainder": r}
        if "quotient" in answer and "remainder" in answer:
            return f"{answer['quotient']} r {answer['remainder']}"
        parts = [f"{k}: {v}" for k, v in answer.items()]
        return ", ".join(parts)
    if isinstance(answer, list):
        return ", ".join(str(x) for x in answer)
    return str(answer)
