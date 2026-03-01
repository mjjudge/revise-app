"""Question & Attempt models — tracks generated instances and student responses."""

import json
from datetime import datetime, timezone
from typing import Any, Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship


class QuestionInstance(SQLModel, table=True):
    """A single generated question.

    The full parameterised payload is stored as JSON so the exact
    question can be re-displayed and audited.
    """

    __tablename__ = "question_instance"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: str = Field(index=True, description="Matches templates YAML id")
    skill: str = Field(index=True, description="Skill code, e.g. stats.mean.basic")
    chapter: Optional[int] = Field(default=None, description="Chapter number (maths) or null for other subjects")
    difficulty: int = Field(description="Template difficulty band 1-5")
    seed: int = Field(description="RNG seed for reproducibility")
    prompt_rendered: str = Field(description="Fully rendered question text")
    payload_json: str = Field(description="JSON: generated parameters")
    correct_json: str = Field(description="JSON: expected answer(s)")
    assets_html: str = Field(default="", description="Pre-rendered HTML/SVG assets")
    hints_used: int = Field(default=0, description="Number of tutor hints consumed")
    fun_prompt: Optional[str] = Field(default=None, description="Fun-rewritten prompt (cached from OpenAI)")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    attempts: List["Attempt"] = Relationship(back_populates="question")

    # Convenience properties
    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)

    @property
    def correct(self) -> Any:
        return json.loads(self.correct_json)


class Attempt(SQLModel, table=True):
    """A student's answer to a question instance."""

    __tablename__ = "attempt"

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question_instance.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    answer_raw: str = Field(description="Raw student answer as typed")
    is_correct: bool = Field(default=False)
    score: float = Field(default=0.0, description="0.0 – 1.0 (partial credit)")
    xp_earned: int = Field(default=0, description="XP awarded for this attempt")
    gold_earned: int = Field(default=0, description="Gold awarded for this attempt")
    feedback: str = Field(default="", description="Short feedback message")
    attempt_number: int = Field(default=1, description="1st, 2nd, 3rd try")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    question: Optional[QuestionInstance] = Relationship(back_populates="attempts")


class UserSkillProgress(SQLModel, table=True):
    """Tracks per-user, per-skill adaptive difficulty state."""

    __tablename__ = "user_skill_progress"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    skill: str = Field(index=True, description="Skill code")
    current_band: int = Field(default=2, description="Current difficulty band 1-5")
    attempts_total: int = Field(default=0)
    attempts_correct: int = Field(default=0)
    streak: int = Field(default=0, description="Consecutive correct (resets on wrong)")
    last_attempted: Optional[datetime] = Field(default=None)

    class Config:
        # Unique constraint on (user_id, skill)
        pass


class SubjectProgress(SQLModel, table=True):
    """Denormalised per-user, per-subject stats — incremented in real time."""

    __tablename__ = "subject_progress"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    subject: str = Field(index=True, description="Subject code (maths, geography, ...)")
    xp_earned: int = Field(default=0, description="Total XP earned in this subject")
    gold_earned: int = Field(default=0, description="Total gold earned in this subject")
    quests_completed: int = Field(default=0, description="Finished quests in this subject")
    questions_answered: int = Field(default=0, description="Total questions answered")
    questions_correct: int = Field(default=0, description="Correct (first try) answers")
    best_streak: int = Field(default=0, description="Best streak in this subject")
    last_played: Optional[datetime] = Field(default=None, description="Last activity time")
