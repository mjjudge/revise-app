"""Admin API routes — stats, payouts, reward controls.

All routes require an authenticated admin session.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.core.config import settings
from app.db.session import get_session
from app.models.quest import Payout, QuestSession
from app.models.question import Attempt, UserSkillProgress
from app.models.user import Role, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory="app/templates/html")


def _get_kid(db: Session) -> User | None:
    """Get the kid user (Anna)."""
    stmt = select(User).where(User.role == Role.kid)
    return db.exec(stmt).first()


# ---------------------------------------------------------------------------
# GET /admin/stats — JSON stats for HTMX
# ---------------------------------------------------------------------------

@router.get("/stats")
def admin_stats(
    request: Request,
    session: Session = Depends(get_session),
):
    """Return child stats as JSON for admin dashboard."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return {"error": "unauthorized"}

    kid = _get_kid(session)
    if not kid:
        return {"xp": 0, "gold": 0, "quests": 0, "accuracy": 0}

    # Count completed quests
    quest_count = session.exec(
        select(func.count(QuestSession.id)).where(
            QuestSession.user_id == kid.id,
            QuestSession.finished == True,  # noqa: E712
        )
    ).one()

    # Overall accuracy
    total_attempts = session.exec(
        select(func.count(Attempt.id)).where(Attempt.user_id == kid.id)
    ).one()
    correct_attempts = session.exec(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == kid.id,
            Attempt.is_correct == True,  # noqa: E712
        )
    ).one()
    accuracy = int((correct_attempts / total_attempts * 100)) if total_attempts else 0

    # Skill progress
    skills = session.exec(
        select(UserSkillProgress).where(UserSkillProgress.user_id == kid.id)
    ).all()
    skill_data = [
        {
            "skill": s.skill,
            "band": s.current_band,
            "total": s.attempts_total,
            "correct": s.attempts_correct,
            "streak": s.streak,
        }
        for s in skills
    ]

    # Recent payouts
    payouts = session.exec(
        select(Payout).where(Payout.user_id == kid.id).order_by(Payout.created_at.desc()).limit(10)  # type: ignore[union-attr]
    ).all()
    payout_data = [
        {
            "gold": p.gold_amount,
            "cash_pence": p.cash_pence,
            "note": p.note,
            "date": p.created_at.strftime("%d %b %Y"),
        }
        for p in payouts
    ]

    # Total paid out
    total_paid = session.exec(
        select(func.coalesce(func.sum(Payout.cash_pence), 0)).where(
            Payout.user_id == kid.id
        )
    ).one()

    return {
        "xp": kid.xp,
        "gold": kid.gold,
        "quests_completed": quest_count,
        "accuracy": accuracy,
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "skills": skill_data,
        "payouts": payout_data,
        "total_paid_pence": int(total_paid),
        "gold_to_pence": settings.gold_to_pence,
        "weekly_gold_cap": settings.weekly_gold_cap,
    }


# ---------------------------------------------------------------------------
# POST /admin/payout — record a gold→cash payout
# ---------------------------------------------------------------------------

@router.post("/payout", response_class=HTMLResponse)
def admin_payout(
    request: Request,
    gold_amount: int = Form(...),
    note: str = Form(default=""),
    session: Session = Depends(get_session),
):
    """Record a payout: deduct gold from kid, record cash equivalent."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return RedirectResponse(url="/login", status_code=303)

    kid = _get_kid(session)
    if not kid:
        return RedirectResponse(url="/admin", status_code=303)

    # Clamp to available gold
    actual_gold = min(gold_amount, kid.gold)
    if actual_gold <= 0:
        return RedirectResponse(url="/admin", status_code=303)

    cash_pence = actual_gold * settings.gold_to_pence

    payout = Payout(
        user_id=kid.id,
        gold_amount=actual_gold,
        cash_pence=cash_pence,
        note=note,
        created_by=user.id,
    )
    kid.gold -= actual_gold
    session.add(payout)
    session.add(kid)
    session.commit()

    return RedirectResponse(url="/admin", status_code=303)


# ---------------------------------------------------------------------------
# POST /admin/settings — update reward settings
# ---------------------------------------------------------------------------

@router.post("/settings", response_class=HTMLResponse)
def admin_settings(
    request: Request,
    weekly_gold_cap: int = Form(default=100),
    session: Session = Depends(get_session),
):
    """Update admin-configurable settings (in-memory, not persisted to env)."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return RedirectResponse(url="/login", status_code=303)

    # Update settings in-memory (resets on restart)
    settings.weekly_gold_cap = weekly_gold_cap

    return RedirectResponse(url="/admin", status_code=303)
