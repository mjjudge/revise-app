"""Page routes — serve HTML via Jinja2 templates."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.core.config import settings
from app.db.session import get_session
from app.services.auth import get_current_user, greeting
from app.models.quest import Payout, QuestSession
from app.models.question import Attempt, UserSkillProgress
from app.models.user import Role, User

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates/html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: int = 0):
    """Show the login / user-select page."""
    return templates.TemplateResponse(request, "login.html", {
        "error": bool(error),
    })


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, session: Session = Depends(get_session)):
    """Child's home page — quest launcher."""
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(request, "home.html", {
        "user": user,
        "greeting": greeting(),
    })


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, session: Session = Depends(get_session)):
    """Admin dashboard — progress + reward controls."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return RedirectResponse(url="/login", status_code=303)

    # Gather stats for the kid user
    kid = session.exec(select(User).where(User.role == Role.kid)).first()
    stats = {"xp": 0, "gold": 0, "quests_completed": 0, "accuracy": 0,
             "total_paid_pence": 0, "payouts": []}

    if kid:
        stats["xp"] = kid.xp
        stats["gold"] = kid.gold

        quest_count = session.exec(
            select(func.count(QuestSession.id)).where(
                QuestSession.user_id == kid.id,
                QuestSession.finished == True,  # noqa: E712
            )
        ).one()
        stats["quests_completed"] = quest_count

        total_att = session.exec(
            select(func.count(Attempt.id)).where(Attempt.user_id == kid.id)
        ).one()
        correct_att = session.exec(
            select(func.count(Attempt.id)).where(
                Attempt.user_id == kid.id,
                Attempt.is_correct == True,  # noqa: E712
            )
        ).one()
        stats["accuracy"] = int(correct_att / total_att * 100) if total_att else 0

        total_paid = session.exec(
            select(func.coalesce(func.sum(Payout.cash_pence), 0)).where(
                Payout.user_id == kid.id
            )
        ).one()
        stats["total_paid_pence"] = int(total_paid)

        payouts = session.exec(
            select(Payout).where(Payout.user_id == kid.id)
            .order_by(Payout.created_at.desc()).limit(10)  # type: ignore[union-attr]
        ).all()
        stats["payouts"] = [
            {"gold": p.gold_amount, "cash_pence": p.cash_pence, "note": p.note,
             "date": p.created_at.strftime("%d %b %Y")}
            for p in payouts
        ]

    return templates.TemplateResponse(request, "admin.html", {
        "user": user,
        "stats": stats,
        "gold_to_pence": settings.gold_to_pence,
        "weekly_gold_cap": settings.weekly_gold_cap,
    })
