"""User model — simple two-user system (kid + admin)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class Role(str, Enum):
    kid = "kid"
    admin = "admin"


class User(SQLModel, table=True):
    """A user of the app. For MVP, just Anna (kid) and Parent (admin)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    display_name: str = Field(index=True)
    role: Role = Field(default=Role.kid)
    pin_hash: str = Field(description="bcrypt hash of the 4-digit PIN")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    xp: int = Field(default=0, description="Total experience points")
    gold: int = Field(default=0, description="Gold coins balance")
