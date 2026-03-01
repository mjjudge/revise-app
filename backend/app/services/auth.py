"""Authentication service — PIN verification + session management."""

import random
from datetime import datetime, timedelta
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlmodel import Session, select
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.db.seed import verify_pin
from app.models.user import User, Role

SESSION_COOKIE = "revise_session"

_serializer = URLSafeTimedSerializer(settings.secret_key)


def _greet_name() -> str:
    """Pick a greeting name — mostly the child's name, occasionally a nickname."""
    names = [settings.child_name] * 3 + settings.nickname_list
    return random.choice(names)


def authenticate(session: Session, display_name: str, pin: str) -> Optional[User]:
    """Verify a user's PIN and return the User if valid, else None."""
    user = session.exec(select(User).where(User.display_name == display_name)).first()
    if user and verify_pin(pin, user.pin_hash):
        return user
    return None


def create_session_cookie(response: Response, user: User) -> None:
    """Set a signed session cookie after successful login."""
    token = _serializer.dumps({"user_id": user.id, "role": user.role.value})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
    )


def get_current_user(request: Request, session: Session) -> Optional[User]:
    """Extract and verify the current user from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        return None
    user = session.get(User, data["user_id"])
    return user


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie."""
    response.delete_cookie(SESSION_COOKIE)


def greeting() -> str:
    """Return a themed greeting for the child."""
    name = _greet_name()
    greetings = [
        f"Welcome back, {name}! Ready for an adventure?",
        f"Hail, brave {name}! Your quest awaits!",
        f"The kingdom needs you, {name}!",
        f"Greetings, {name}! Let's earn some XP!",
        f"Ah, {name}! A new challenge is upon us!",
    ]
    return random.choice(greetings)
