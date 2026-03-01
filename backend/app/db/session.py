"""Database engine and session management."""

import logging
from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Import models so SQLModel.metadata knows about all tables
import app.models.user  # noqa: F401
import app.models.question  # noqa: F401
import app.models.quest  # noqa: F401

# SQLite needs check_same_thread=False for FastAPI's async context
connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, echo=(settings.app_env == "dev"), connect_args=connect_args)

# ---------------------------------------------------------------------------
# Schema migrations – idempotent ALTER TABLE statements for columns added
# after the initial schema was created.  Each entry is (table, column, type).
# ---------------------------------------------------------------------------
_MIGRATIONS: list[tuple[str, str, str]] = [
    ("question_instance", "hints_used", "INTEGER DEFAULT 0"),
    ("question_instance", "fun_prompt", "TEXT"),
    ("quest_session", "subject", "TEXT"),
    ("quest_session", "unit", "TEXT"),
]


def _run_migrations() -> None:
    """Apply any pending column additions.  Safe to call every startup."""
    with engine.connect() as conn:
        for table, column, col_type in _MIGRATIONS:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                ))
                conn.commit()
                logger.info("migration: added column %s.%s", table, column)
            except Exception:
                # Column already exists – nothing to do
                conn.rollback()


def init_db() -> None:
    """Create all tables and apply migrations. Called on app startup."""
    SQLModel.metadata.create_all(engine)
    _run_migrations()


def get_session():
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session
