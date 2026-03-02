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
from app.services.questions import get_all_subject_progress, get_subject_progress, get_skill_insights, get_boosted_skills
from app.services.game_config import get_all_games_status, get_enabled_games, toggle_game

router = APIRouter(tags=["pages"])

templates = __import__("app.templates.shared", fromlist=["create_templates"]).create_templates()

# ── Subject metadata (icons, unit definitions, etc.) ──────────────────────

_SUBJECT_META: dict[str, dict] = {
    "maths": {
        "title": "Maths",
        "icon": "🧮",
        "units": [
            {
                "key": "data", "chapter": 5,
                "title": "Data & Charts",
                "icon": "📊",
                "bg_class": "bg-blue-600/30",
                "description": "Averages, pie charts, time series & more",
                "href": "/quest/chapter/5",
            },
            {
                "key": "algebra", "chapter": 6,
                "title": "Expressions & Formulae",
                "icon": "🧮",
                "bg_class": "bg-emerald-600/30",
                "description": "Substitution, simplify, like terms",
                "href": "/quest/chapter/6",
            },
            {
                "key": "calculation", "chapter": 7,
                "title": "Calculation & Measure",
                "icon": "🧠",
                "bg_class": "bg-amber-600/30",
                "description": "Conversions, rounding, BIDMAS, mental methods",
                "href": "/quest/chapter/7",
            },
            {
                "key": "probability", "chapter": 8,
                "title": "Probability",
                "icon": "🎲",
                "bg_class": "bg-purple-600/30",
                "description": "Scales, equally likely, experimental probability",
                "href": "/quest/chapter/8",
            },
        ],
    },
    "geography": {
        "title": "Geography",
        "icon": "🌍",
        "units": [
            {
                "key": "maps",
                "title": "Maps & Navigation",
                "icon": "🗺️",
                "bg_class": "bg-emerald-600/30",
                "description": "Grid refs, compass, scale, contours & cross-sections",
                "href": "/quest/unit/geography/maps",
            },
            {
                "key": "weather",
                "title": "Weather",
                "icon": "🌦️",
                "bg_class": "bg-blue-600/30",
                "description": "Instruments, air masses, clouds, pressure & rainfall",
                "href": "/quest/unit/geography/weather",
            },
            {
                "key": "climate",
                "title": "Climate",
                "icon": "🌡️",
                "bg_class": "bg-amber-600/30",
                "description": "Climate graphs, impacts & heatwaves",
                "href": "/quest/unit/geography/climate",
            },
            {
                "key": "world",
                "title": "World Knowledge",
                "icon": "🌐",
                "bg_class": "bg-purple-600/30",
                "description": "Continents, oceans & global features",
                "href": "/quest/unit/geography/world",
            },
        ],
    },
}


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: int = 0):
    """Show the login / user-select page."""
    return templates.TemplateResponse(request, "login.html", {
        "error": bool(error),
    })


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, session: Session = Depends(get_session)):
    """Child's home page — subject dashboard."""
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    quests_done = session.exec(
        select(func.count(QuestSession.id)).where(
            QuestSession.user_id == user.id,
            QuestSession.finished == True,  # noqa: E712
        )
    ).one()

    subject_stats = get_all_subject_progress(session, user.id)

    return templates.TemplateResponse(request, "home.html", {
        "user": user,
        "greeting": greeting(),
        "quests_done": quests_done,
        "subject_stats": subject_stats,
    })


@router.get("/subject/{name}", response_class=HTMLResponse)
def subject_home(name: str, request: Request, session: Session = Depends(get_session)):
    """Subject landing page — shows units for a subject."""
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    meta = _SUBJECT_META.get(name)
    if not meta:
        return RedirectResponse(url="/", status_code=303)

    quests_done = session.exec(
        select(func.count(QuestSession.id)).where(
            QuestSession.user_id == user.id,
            QuestSession.finished == True,  # noqa: E712
        )
    ).one()

    sp = get_subject_progress(session, user.id, name)

    return templates.TemplateResponse(request, "subject_home.html", {
        "user": user,
        "subject_title": meta["title"],
        "subject_icon": meta["icon"],
        "subject_name": name,
        "units": meta["units"],
        "quests_done": quests_done,
        "sp": sp,
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

    subject_stats = {}
    skill_insights = {}
    boosted_skills: set[str] = set()
    if kid:
        stats["xp"] = kid.xp
        stats["gold"] = kid.gold
        subject_stats = get_all_subject_progress(session, kid.id)
        skill_insights = get_skill_insights(session, kid.id)
        boosted_skills = get_boosted_skills(session, kid.id)

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
        "subject_stats": subject_stats,
        "skill_insights": skill_insights,
        "boosted_skills": boosted_skills,
        "gold_to_pence": settings.gold_to_pence,
        "weekly_gold_cap": settings.weekly_gold_cap,
    })


@router.get("/admin/games", response_class=HTMLResponse)
def admin_games_page(request: Request, session: Session = Depends(get_session)):
    """Admin page to preview and toggle reward mini-games."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(request, "admin_games.html", {
        "user": user,
        "games": get_all_games_status(),
    })


@router.post("/admin/games/toggle")
async def admin_toggle_game(request: Request, session: Session = Depends(get_session)):
    """Toggle a game on/off. Accepts JSON body {game_id, enabled}."""
    from starlette.responses import JSONResponse

    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return JSONResponse({"status": "error", "msg": "forbidden"}, status_code=403)

    body = await request.json()
    game_id = body.get("game_id", "")
    enabled = body.get("enabled", True)

    ok = toggle_game(game_id, enabled)
    if not ok:
        return JSONResponse({"status": "error", "msg": "unknown game"}, status_code=400)
    return JSONResponse({"status": "ok"})
