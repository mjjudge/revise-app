"""Quest API routes — generate questions, submit answers, get results.

All routes require an authenticated kid session.
Responses are HTMX-friendly HTML fragments.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.question import QuestionInstance, Attempt
from app.models.user import Role
from app.services.auth import get_current_user
from app.services.questions import generate_question, check_answer
from app.templates.feed_loader import get_templates_by_chapter, get_skill_map

router = APIRouter(prefix="/quest", tags=["quest"])

templates = Jinja2Templates(directory="app/templates/html")


# ---------------------------------------------------------------------------
# GET /quest/chapter/{chapter} — start a quest (pick skill / question)
# ---------------------------------------------------------------------------

@router.get("/chapter/{chapter}", response_class=HTMLResponse)
def quest_chapter(
    chapter: int,
    request: Request,
    session: Session = Depends(get_session),
):
    """Show available skills for a chapter."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    chapter_templates = get_templates_by_chapter(chapter)
    skill_map = get_skill_map()

    # Group by skill
    skills_in_chapter: dict[str, str] = {}
    for t in chapter_templates:
        if t.skill not in skills_in_chapter:
            skill_def = skill_map.get(t.skill)
            skills_in_chapter[t.skill] = skill_def.name if skill_def else t.skill

    return templates.TemplateResponse(request, "quest_chapter.html", {
        "user": user,
        "chapter": chapter,
        "skills": skills_in_chapter,
    })


# ---------------------------------------------------------------------------
# POST /quest/generate — generate a new question
# ---------------------------------------------------------------------------

@router.post("/generate", response_class=HTMLResponse)
def quest_generate(
    request: Request,
    skill: str = Form(default=None),
    chapter: int = Form(default=None),
    template_id: str = Form(default=None),
    session: Session = Depends(get_session),
):
    """Generate a question and show it."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    instance = generate_question(
        session, user,
        skill=skill,
        chapter=chapter,
        template_id=template_id,
    )

    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
    })


# ---------------------------------------------------------------------------
# POST /quest/answer — submit an answer
# ---------------------------------------------------------------------------

@router.post("/answer", response_class=HTMLResponse)
def quest_answer(
    request: Request,
    question_id: int = Form(...),
    answer: str = Form(...),
    session: Session = Depends(get_session),
):
    """Check the student's answer and return feedback."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    attempt, result = check_answer(session, user, question_id, answer)

    # Refresh user to get updated XP/gold
    session.refresh(user)

    return templates.TemplateResponse(request, "quest_result.html", {
        "user": user,
        "question": attempt.question,
        "attempt": attempt,
        "result": {
            "correct": result.correct,
            "score": result.score,
            "feedback": result.feedback,
            "expected": result.expected,
        },
        "can_retry": not result.correct and attempt.attempt_number < 3,
    })
