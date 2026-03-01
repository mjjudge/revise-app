"""Database engine and session management."""

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

# Import models so SQLModel.metadata knows about all tables
import app.models.user  # noqa: F401
import app.models.question  # noqa: F401

# SQLite needs check_same_thread=False for FastAPI's async context
connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, echo=(settings.app_env == "dev"), connect_args=connect_args)


def init_db() -> None:
    """Create all tables. Called on app startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session
