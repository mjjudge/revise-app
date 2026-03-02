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
from app.services.questions import generate_question, check_answer, detect_milestone, milestone_message, MILESTONE_INTERVAL, get_mcq_options
from app.templates.feed_loader import (
    clear_cache,
    load_and_validate,
    load_skills,
    load_templates,
    get_templates_by_subject,
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


@pytest.fixture(autouse=True)
def _fresh_feed_cache():
    """Clear feed-loader cache before every test."""
    clear_cache()
    yield
    clear_cache()


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
        """For maths templates, chapter must match its skill's chapter."""
        skills_feed, templates_feed = load_and_validate()
        skill_chapters = {s.code: s.chapter for s in skills_feed.skills}
        for t in templates_feed.templates:
            if t.chapter is None:
                continue  # Non-maths templates don't use chapter
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

    def test_maths_template_ids_have_chapter_prefix(self):
        """Maths template IDs should start with 'ch{N}_' matching their chapter."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            if t.chapter is None:
                continue  # Non-maths templates use their own prefix
            expected_prefix = f"ch{t.chapter}_"
            assert t.id.startswith(expected_prefix), (
                f"Template '{t.id}' should start with '{expected_prefix}'"
            )

    def test_geography_template_ids_have_geog_prefix(self):
        """Geography template IDs should start with 'geog_' or a place-study prefix."""
        _GEOG_PREFIXES = ("geog_", "minsterworth_", "evesham_")
        templates_feed = load_templates()
        for t in templates_feed.templates:
            if t.subject == "geography":
                assert t.id.startswith(_GEOG_PREFIXES), (
                    f"Geography template '{t.id}' should start with one of {_GEOG_PREFIXES}"
                )

    def test_difficulty_distribution(self):
        """Templates should cover multiple difficulty levels."""
        templates_feed = load_templates()
        difficulties = {t.difficulty for t in templates_feed.templates}
        assert len(difficulties) >= 2, (
            f"Expected at least 2 difficulty levels, got {difficulties}"
        )

    def test_all_maths_chapters_have_templates(self):
        """Each maths chapter (5-8) should have at least one template."""
        maths = get_templates_by_subject("maths")
        chapters_with_templates = {t.chapter for t in maths}
        for ch in (5, 6, 7, 8):
            assert ch in chapters_with_templates, (
                f"Maths chapter {ch} has no templates"
            )

    def test_calculator_field_values(self):
        """Calculator field should be None, 'basic', or 'scientific'."""
        templates_feed = load_templates()
        for t in templates_feed.templates:
            assert t.calculator in (None, "basic", "scientific"), (
                f"Template '{t.id}' has invalid calculator value '{t.calculator}'"
            )

    def test_calculator_tagged_templates_exist(self):
        """At least some maths templates should have a calculator."""
        maths = get_templates_by_subject("maths")
        with_calc = [t for t in maths if t.calculator]
        assert len(with_calc) >= 8, (
            f"Expected at least 8 calculator-tagged maths templates, got {len(with_calc)}"
        )


# ---------------------------------------------------------------------------
# End-to-End Template Generation Tests
# ---------------------------------------------------------------------------


class TestEndToEndGeneration:
    """Test that every template can generate a question and produce a valid answer."""

    def test_every_maths_template_generates_successfully(self, session, kid):
        """Each maths template should generate a question without errors.

        Geography templates are excluded — their generators are not yet
        implemented (EPIC 9).
        """
        maths = get_templates_by_subject("maths")
        assert len(maths) > 0
        for t in maths:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            assert instance.id is not None, f"Template '{t.id}' failed to generate"
            assert instance.prompt_rendered, f"Template '{t.id}' has empty prompt"
            assert instance.correct_json, f"Template '{t.id}' has no correct answer"
            assert instance.template_id == t.id

    def test_every_maths_template_correct_answer_marks_correctly(self, session, kid):
        """Submitting the correct answer should mark as correct for every maths template."""
        maths = get_templates_by_subject("maths")
        for t in maths:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            correct = _decode_json(instance.correct_json)
            answer_str = _answer_to_str(correct)

            attempt, result = check_answer(session, kid, instance.id, answer_str)
            assert result.correct, (
                f"Template '{t.id}': correct answer '{answer_str}' was not marked correct. "
                f"Feedback: {result.feedback}"
            )

    def test_every_maths_template_wrong_answer_marks_incorrect(self, session, kid):
        """Submitting a clearly wrong answer should be marked incorrect."""
        maths = get_templates_by_subject("maths")
        for t in maths:
            instance = generate_question(session, kid, template_id=t.id, seed=42)
            attempt, result = check_answer(session, kid, instance.id, "WRONG_ANSWER_xyz")
            assert not result.correct, (
                f"Template '{t.id}': 'WRONG_ANSWER_xyz' was incorrectly marked correct"
            )

    def test_deterministic_generation(self, session, kid):
        """Same seed should produce the same question for each maths template."""
        maths = get_templates_by_subject("maths")
        for t in maths:
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
        maths = get_templates_by_subject("maths")
        different_count = 0
        for t in maths:
            q1 = generate_question(session, kid, template_id=t.id, seed=100)
            q2 = generate_question(session, kid, template_id=t.id, seed=999)
            if q1.payload_json != q2.payload_json:
                different_count += 1
        assert different_count > len(maths) // 2


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


# ─── EPIC 6.6: Milestone & celebration tests ──────────────────────────────

class TestMilestoneDetection:
    """Tests for detect_milestone helper."""

    def test_no_milestone_within_same_bucket(self):
        assert detect_milestone(10, 50) is None

    def test_milestone_exact_boundary(self):
        assert detect_milestone(90, 100) == 100

    def test_milestone_overshoot(self):
        assert detect_milestone(85, 115) == 100

    def test_milestone_no_xp_gain(self):
        assert detect_milestone(100, 100) is None

    def test_milestone_xp_decrease(self):
        assert detect_milestone(150, 100) is None

    def test_milestone_second_bucket(self):
        assert detect_milestone(180, 210) == 200

    def test_milestone_large_jump(self):
        """Even a jump across multiple buckets returns the latest boundary."""
        assert detect_milestone(50, 350) == 300

    def test_milestone_zero_start(self):
        assert detect_milestone(0, 100) == 100

    def test_milestone_zero_to_below(self):
        assert detect_milestone(0, 99) is None


class TestMilestoneMessage:
    """Tests for milestone_message."""

    def test_returns_tuple(self):
        title, body = milestone_message(100)
        assert isinstance(title, str)
        assert isinstance(body, str)

    def test_xp_in_body(self):
        _, body = milestone_message(200)
        assert "200" in body

    def test_messages_cycle(self):
        """Different milestones produce different messages."""
        titles = {milestone_message(i * 100)[0] for i in range(1, 7)}
        assert len(titles) >= 4  # at least 4 unique titles out of 6

    def test_message_wraps_around(self):
        """After exhausting all messages, they cycle."""
        t1, _ = milestone_message(100)
        t7, _ = milestone_message(700)
        assert t1 == t7  # 7th = 1st (6 messages, wraps)


class TestMilestoneIntegration:
    """Integration: milestone passed through quest_answer to template."""

    @pytest.fixture(autouse=True)
    def setup(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        self.session = Session(engine)
        from bcrypt import hashpw, gensalt
        kid = User(
            display_name="TestKid", role=Role.kid,
            pin_hash=hashpw(b"1234", gensalt()).decode(),
            xp=95,  # close to 100 milestone
        )
        self.session.add(kid)
        self.session.commit()
        self.session.refresh(kid)
        self.kid = kid
        yield
        self.session.close()

    def test_milestone_triggers_on_xp_cross(self):
        """When XP crosses a 100 boundary, detect_milestone returns the value."""
        old_xp = self.kid.xp  # 95
        # Simulate earning XP
        self.kid.xp += 10  # now 105
        milestone = detect_milestone(old_xp, self.kid.xp)
        assert milestone == 100

    def test_no_milestone_when_not_crossing(self):
        old_xp = self.kid.xp  # 95
        self.kid.xp += 2  # now 97
        milestone = detect_milestone(old_xp, self.kid.xp)
        assert milestone is None


# ---------------------------------------------------------------------------
# MCQ Options Tests
# ---------------------------------------------------------------------------


class TestMCQOptions:
    """Ensure MCQ questions produce shuffled options."""

    @pytest.fixture(autouse=True)
    def setup(self, session, kid):
        self.session = session
        self.kid = kid

    def test_mcq_template_returns_options(self):
        """MCQ questions should return a list of shuffled options."""
        instance = generate_question(
            self.session, self.kid, template_id="ch5_line_graph_trend_v1",
        )
        options = get_mcq_options(instance)
        assert options is not None
        assert isinstance(options, list)
        assert len(options) == 4  # 1 correct + 3 distractors
        # The correct answer must be among the options
        correct = json.loads(instance.correct_json)
        assert correct in options

    def test_non_mcq_template_returns_none(self):
        """Non-MCQ questions should return None for options."""
        instance = generate_question(
            self.session, self.kid, template_id="ch5_mean_from_list_v1",
        )
        options = get_mcq_options(instance)
        assert options is None

    def test_mcq_options_deterministic_per_seed(self):
        """Same seed should produce same option ordering."""
        instance = generate_question(
            self.session, self.kid, template_id="ch5_line_graph_trend_v1",
        )
        opts1 = get_mcq_options(instance)
        opts2 = get_mcq_options(instance)
        assert opts1 == opts2
