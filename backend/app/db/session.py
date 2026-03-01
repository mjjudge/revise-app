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

        # ── Make question_instance.chapter nullable ──────────────────
        # SQLite doesn't support ALTER COLUMN, so we recreate the table.
        # Only runs when the column is still NOT NULL.
        try:
            row = conn.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='question_instance'"
            )).fetchone()
            if row and "chapter INTEGER NOT NULL" in (row[0] or ""):
                logger.info("migration: making question_instance.chapter nullable")
                conn.execute(text("""
                    CREATE TABLE question_instance_new (
                        id INTEGER PRIMARY KEY,
                        template_id VARCHAR NOT NULL,
                        skill VARCHAR NOT NULL,
                        chapter INTEGER,
                        difficulty INTEGER NOT NULL,
                        seed INTEGER NOT NULL,
                        prompt_rendered VARCHAR NOT NULL,
                        payload_json VARCHAR NOT NULL,
                        correct_json VARCHAR NOT NULL,
                        assets_html VARCHAR NOT NULL DEFAULT '',
                        hints_used INTEGER NOT NULL DEFAULT 0,
                        fun_prompt VARCHAR,
                        user_id INTEGER REFERENCES "user"(id),
                        created_at TIMESTAMP NOT NULL
                    )
                """))
                conn.execute(text("""
                    INSERT INTO question_instance_new
                    SELECT id, template_id, skill, chapter, difficulty, seed,
                           prompt_rendered, payload_json, correct_json,
                           assets_html, hints_used, fun_prompt, user_id, created_at
                    FROM question_instance
                """))
                conn.execute(text("DROP TABLE question_instance"))
                conn.execute(text("ALTER TABLE question_instance_new RENAME TO question_instance"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_question_instance_template_id ON question_instance(template_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_question_instance_skill ON question_instance(skill)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_question_instance_user_id ON question_instance(user_id)"))
                conn.commit()
                logger.info("migration: question_instance.chapter is now nullable")
        except Exception as e:
            conn.rollback()
            logger.warning("migration: chapter nullable check failed: %s", e)


def init_db() -> None:
    """Create all tables and apply migrations. Called on app startup."""
    SQLModel.metadata.create_all(engine)
    _run_migrations()


def get_session():
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session
