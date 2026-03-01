"""Seed the database with initial users on first run."""

import bcrypt
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import engine
from app.models.user import User, Role


def hash_pin(pin: str) -> str:
    """Hash a PIN with bcrypt."""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(plain: str, hashed: str) -> bool:
    """Verify a PIN against its bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def seed_users() -> None:
    """Create the default kid + admin users if they don't exist."""
    with Session(engine) as session:
        existing = session.exec(select(User)).all()
        if existing:
            return  # already seeded

        kid = User(
            display_name=settings.child_name,
            role=Role.kid,
            pin_hash=hash_pin(settings.kid_pin),
        )
        admin = User(
            display_name="Parent",
            role=Role.admin,
            pin_hash=hash_pin(settings.admin_pin),
        )
        session.add(kid)
        session.add(admin)
        session.commit()
