"""Quest session & payout models — tracks quest loops and gold-to-cash payouts."""

from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class QuestSession(SQLModel, table=True):
    """A quest is a loop of 8-10 questions from a chapter/skill/unit."""

    __tablename__ = "quest_session"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    chapter: int = Field(default=0, description="Chapter number (maths)")
    skill: Optional[str] = Field(default=None, description="Skill code if skill quest, null for chapter/unit quest")
    subject: Optional[str] = Field(default=None, description="Subject code (e.g. geography)")
    unit: Optional[str] = Field(default=None, description="Unit key for unit quests")
    total_questions: int = Field(description="Target questions in this quest (8 or 10)")
    completed: int = Field(default=0, description="Questions answered so far")
    correct: int = Field(default=0, description="Questions answered correctly (first try)")
    xp_earned: int = Field(default=0, description="Total XP earned in this quest")
    gold_earned: int = Field(default=0, description="Total gold earned in this quest")
    streak: int = Field(default=0, description="Current consecutive correct within quest")
    best_streak: int = Field(default=0, description="Best streak achieved in quest")
    finished: bool = Field(default=False, description="Whether all questions answered")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default=None)

    # Track which question IDs belong to this quest (comma-separated)
    question_ids: str = Field(default="", description="Comma-separated list of question_instance ids")

    def add_question_id(self, qid: int) -> None:
        ids = self.question_ids.split(",") if self.question_ids else []
        ids.append(str(qid))
        self.question_ids = ",".join(ids)

    def get_question_ids(self) -> list[int]:
        if not self.question_ids:
            return []
        return [int(x) for x in self.question_ids.split(",") if x]


class Payout(SQLModel, table=True):
    """Records when parent converts gold to pocket money."""

    __tablename__ = "payout"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    gold_amount: int = Field(description="Gold deducted from balance")
    cash_pence: int = Field(description="Cash value in pence")
    note: str = Field(default="", description="Optional note from parent")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: int = Field(description="Admin user ID who recorded payout")
