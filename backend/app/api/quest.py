"""Quest API routes — quest loop, answer submission, summary.

Supports two quest modes:
  - Skill quest: 8 questions from a single skill
  - Chapter quest: 10 questions mixed across chapter skills

Flow: POST /quest/start → question page → POST /quest/answer → result →
      (loop until done) → GET /quest/summary/{id}
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.quest import QuestSession, Payout
from app.models.question import QuestionInstance, Attempt
from app.models.user import Role, User
from app.services.auth import get_current_user
from app.services.questions import generate_question, check_answer
from app.templates.feed_loader import get_templates_by_chapter, get_skill_map

router = APIRouter(prefix="/quest", tags=["quest"])

templates = Jinja2Templates(directory="app/templates/html")


# ---------------------------------------------------------------------------
# GET /quest/chapter/{chapter} — pick skill or start chapter quest
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
# POST /quest/start — begin a quest (skill or chapter)
# ---------------------------------------------------------------------------

@router.post("/start", response_class=HTMLResponse)
def quest_start(
    request: Request,
    skill: str = Form(default=None),
    chapter: int = Form(default=None),
    session: Session = Depends(get_session),
):
    """Start a new quest session and show the first question."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    # Skill quest = 8 Qs, chapter quest = 10 Qs
    if skill:
        total_q = 8
    else:
        total_q = 10

    quest = QuestSession(
        user_id=user.id,
        chapter=chapter or 0,
        skill=skill,
        total_questions=total_q,
    )
    session.add(quest)
    session.commit()
    session.refresh(quest)

    # Generate first question
    instance = generate_question(
        session, user,
        skill=skill,
        chapter=chapter,
    )
    quest.add_question_id(instance.id)
    quest.completed = 0  # not yet answered
    session.add(quest)
    session.commit()

    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
        "quest": quest,
        "quest_progress": f"Question 1 of {quest.total_questions}",
    })


# ---------------------------------------------------------------------------
# POST /quest/generate — legacy single-question (still useful for retry)
# ---------------------------------------------------------------------------

@router.post("/generate", response_class=HTMLResponse)
def quest_generate(
    request: Request,
    skill: str = Form(default=None),
    chapter: int = Form(default=None),
    template_id: str = Form(default=None),
    session: Session = Depends(get_session),
):
    """Generate a single question (no quest session)."""
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
        "quest": None,
        "quest_progress": "",
    })


# ---------------------------------------------------------------------------
# POST /quest/answer — submit an answer
# ---------------------------------------------------------------------------

@router.post("/answer", response_class=HTMLResponse)
def quest_answer(
    request: Request,
    question_id: int = Form(...),
    answer: str = Form(...),
    quest_id: int = Form(default=0),
    session: Session = Depends(get_session),
):
    """Check the student's answer and return feedback."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    # Load quest session if present
    quest: QuestSession | None = None
    if quest_id:
        quest = session.get(QuestSession, quest_id)

    attempt, result = check_answer(session, user, question_id, answer, quest=quest)

    # Refresh user for updated XP/gold
    session.refresh(user)

    # Update quest session
    if quest:
        quest.completed += 1
        if result.correct:
            quest.correct += 1
        quest.xp_earned += attempt.xp_earned
        quest.gold_earned += attempt.gold_earned

        if quest.completed >= quest.total_questions:
            quest.finished = True
            quest.finished_at = datetime.now(timezone.utc)

        session.add(quest)
        session.commit()

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
        "quest": quest,
        "quest_finished": quest.finished if quest else False,
    })


# ---------------------------------------------------------------------------
# POST /quest/next — generate next question in a quest
# ---------------------------------------------------------------------------

@router.post("/next", response_class=HTMLResponse)
def quest_next(
    request: Request,
    quest_id: int = Form(...),
    session: Session = Depends(get_session),
):
    """Generate the next question in a quest loop."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    quest = session.get(QuestSession, quest_id)
    if not quest or quest.finished:
        return RedirectResponse(url="/", status_code=303)

    instance = generate_question(
        session, user,
        skill=quest.skill,
        chapter=quest.chapter if not quest.skill else None,
    )
    quest.add_question_id(instance.id)
    session.add(quest)
    session.commit()

    q_num = quest.completed + 1  # 1-indexed, completed = answered so far

    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
        "quest": quest,
        "quest_progress": f"Question {q_num} of {quest.total_questions}",
    })


# ---------------------------------------------------------------------------
# GET /quest/summary/{quest_id} — quest completion summary
# ---------------------------------------------------------------------------

@router.get("/summary/{quest_id}", response_class=HTMLResponse)
def quest_summary(
    quest_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    """Show the quest completion summary."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    quest = session.get(QuestSession, quest_id)
    if not quest:
        return RedirectResponse(url="/", status_code=303)

    # Compute accuracy percentage
    accuracy = (quest.correct / quest.total_questions * 100) if quest.total_questions else 0

    # Determine rank based on accuracy
    if accuracy >= 90:
        rank = "Legendary"
        rank_emoji = "👑"
    elif accuracy >= 70:
        rank = "Epic"
        rank_emoji = "⚔️"
    elif accuracy >= 50:
        rank = "Brave"
        rank_emoji = "🛡️"
    else:
        rank = "Apprentice"
        rank_emoji = "📖"

    return templates.TemplateResponse(request, "quest_summary.html", {
        "user": user,
        "quest": quest,
        "accuracy": int(accuracy),
        "rank": rank,
        "rank_emoji": rank_emoji,
    })
