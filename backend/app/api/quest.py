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
from app.services.questions import generate_question, check_answer, detect_milestone, milestone_message, get_mcq_options, get_order_items, get_grid_fill_data
from app.services.tiers import detect_tier_up
from app.templates.feed_loader import get_templates_by_chapter, get_templates_by_unit, get_skill_map, get_template_by_id

router = APIRouter(prefix="/quest", tags=["quest"])

templates = __import__("app.templates.shared", fromlist=["create_templates"]).create_templates()


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
# GET /quest/unit/{subject}/{unit} — pick skill within a unit
# ---------------------------------------------------------------------------

@router.get("/unit/{subject}/{unit}", response_class=HTMLResponse)
def quest_unit(
    subject: str,
    unit: str,
    request: Request,
    session: Session = Depends(get_session),
):
    """Show available skills for a subject unit."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    unit_templates = get_templates_by_unit(subject, unit)
    if not unit_templates:
        return RedirectResponse(url=f"/subject/{subject}", status_code=303)

    skill_map = get_skill_map()
    skills_in_unit: dict[str, str] = {}
    for t in unit_templates:
        if t.skill not in skills_in_unit:
            skill_def = skill_map.get(t.skill)
            skills_in_unit[t.skill] = skill_def.name if skill_def else t.skill

    # Look up unit metadata for display titles
    from app.api.pages import _SUBJECT_META
    subject_meta = _SUBJECT_META.get(subject, {})
    unit_meta = next((u for u in subject_meta.get("units", []) if u["key"] == unit), None)

    return templates.TemplateResponse(request, "quest_unit.html", {
        "user": user,
        "subject": subject,
        "unit": unit,
        "subject_title": subject_meta.get("title", subject.title()),
        "subject_icon": subject_meta.get("icon", "📚"),
        "unit_title": unit_meta["title"] if unit_meta else unit.title(),
        "unit_icon": unit_meta["icon"] if unit_meta else "📖",
        "skills": skills_in_unit,
    })


# ---------------------------------------------------------------------------
# POST /quest/start — begin a quest (skill or chapter)
# ---------------------------------------------------------------------------

@router.post("/start", response_class=HTMLResponse)
def quest_start(
    request: Request,
    skill: str = Form(default=None),
    chapter: int = Form(default=None),
    subject: str = Form(default=None),
    unit: str = Form(default=None),
    session: Session = Depends(get_session),
):
    """Start a new quest session and show the first question."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    # Skill quest = 8 Qs, chapter/unit quest = 10 Qs
    if skill:
        total_q = 8
    else:
        total_q = 10

    quest = QuestSession(
        user_id=user.id,
        chapter=chapter or 0,
        skill=skill,
        subject=subject,
        unit=unit,
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
        subject=subject,
        unit=unit,
    )
    quest.add_question_id(instance.id)
    quest.completed = 0  # not yet answered
    session.add(quest)
    session.commit()

    tpl = get_template_by_id(instance.template_id)
    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
        "quest": quest,
        "quest_progress": f"Question 1 of {quest.total_questions}",
        "calculator": tpl.calculator if tpl else None,
        "mcq_options": get_mcq_options(instance),
        "order_items": get_order_items(instance),
        "grid_fill_data": get_grid_fill_data(instance),
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

    tpl = get_template_by_id(instance.template_id)
    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
        "quest": None,
        "quest_progress": "",
        "calculator": tpl.calculator if tpl else None,
        "mcq_options": get_mcq_options(instance),
        "order_items": get_order_items(instance),
        "grid_fill_data": get_grid_fill_data(instance),
    })


# ---------------------------------------------------------------------------
# POST /quest/answer — submit an answer
# ---------------------------------------------------------------------------

@router.post("/answer", response_class=HTMLResponse)
def quest_answer(
    request: Request,
    question_id: int = Form(...),
    answer: str = Form(""),
    quest_id: int = Form(default=0),
    session: Session = Depends(get_session),
):
    """Check the student's answer and return feedback."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return RedirectResponse(url="/login", status_code=303)

    # Validate non-empty answer
    answer = answer.strip()
    if not answer:
        # Return inline error via HTMX swap
        is_htmx = request.headers.get("hx-request") == "true"
        error_html = (
            '<div id="answer-area">'
            '<p class="text-red-400 text-sm mb-3 font-medium">'
            '⚠️ Please type an answer before submitting!</p>'
            '<form method="post" action="/quest/answer"'
            ' hx-post="/quest/answer" hx-target="#answer-area" hx-swap="outerHTML">'
            f'<input type="hidden" name="question_id" value="{question_id}">'
            f'<input type="hidden" name="quest_id" value="{quest_id}">'
            '<div class="mb-4">'
            '<label for="answer" class="block text-realm-purple-200 text-sm mb-2">Your answer:</label>'
            '<input type="text" id="answer" name="answer" autocomplete="off" autofocus required'
            ' class="w-full px-4 py-3 rounded-xl bg-realm-purple-800/80 border border-red-400'
            ' text-white text-lg placeholder-realm-purple-400 focus:outline-none focus:border-realm-gold-400'
            ' focus:ring-2 focus:ring-realm-gold-400/30"'
            ' placeholder="Type your answer here...">'
            '</div>'
            '<button type="submit"'
            ' class="w-full py-3 bg-realm-gold-500 hover:bg-realm-gold-400 text-realm-purple-900'
            ' font-bold rounded-xl transition-colors text-lg">'
            '⚔️ Submit Answer</button>'
            '</form></div>'
        )
        return HTMLResponse(content=error_html, status_code=200)

    # Load quest session if present
    quest: QuestSession | None = None
    if quest_id:
        quest = session.get(QuestSession, quest_id)

    old_xp = user.xp  # snapshot for milestone detection
    attempt, result = check_answer(session, user, question_id, answer, quest=quest)

    # Refresh user for updated XP/gold
    session.refresh(user)

    # Milestone detection
    milestone_xp = detect_milestone(old_xp, user.xp)
    milestone = None
    if milestone_xp:
        title, body = milestone_message(milestone_xp)
        milestone = {"xp": milestone_xp, "title": title, "body": body}

    # Tier-up detection
    new_tier = detect_tier_up(old_xp, user.xp)
    tier_up = None
    if new_tier:
        tier_up = {
            "title": new_tier.title,
            "icon": new_tier.icon,
            "flavour": new_tier.flavour,
            "accent": new_tier.accent,
        }

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
        "milestone": milestone,
        "tier_up": tier_up,
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
        chapter=quest.chapter if not quest.skill and not quest.unit else None,
        subject=quest.subject,
        unit=quest.unit if not quest.skill else None,
    )
    quest.add_question_id(instance.id)
    session.add(quest)
    session.commit()

    q_num = quest.completed + 1  # 1-indexed, completed = answered so far

    tpl = get_template_by_id(instance.template_id)
    return templates.TemplateResponse(request, "quest_question.html", {
        "user": user,
        "question": instance,
        "attempt_number": 1,
        "quest": quest,
        "quest_progress": f"Question {q_num} of {quest.total_questions}",
        "calculator": tpl.calculator if tpl else None,
        "mcq_options": get_mcq_options(instance),
        "order_items": get_order_items(instance),
        "grid_fill_data": get_grid_fill_data(instance),
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

    # Determine back-link context for subject/unit quests
    back_url = f"/quest/chapter/{quest.chapter}" if quest.chapter else "/"
    back_label = f"Chapter {quest.chapter}" if quest.chapter else "Home"
    if quest.subject and quest.unit:
        back_url = f"/quest/unit/{quest.subject}/{quest.unit}"
        from app.api.pages import _SUBJECT_META
        subject_meta = _SUBJECT_META.get(quest.subject, {})
        unit_meta = next(
            (u for u in subject_meta.get("units", []) if u["key"] == quest.unit),
            None,
        )
        back_label = unit_meta["title"] if unit_meta else quest.unit.replace("_", " ").title()
    elif quest.subject:
        back_url = f"/subject/{quest.subject}"
        back_label = quest.subject.title()

    return templates.TemplateResponse(request, "quest_summary.html", {
        "user": user,
        "quest": quest,
        "accuracy": int(accuracy),
        "rank": rank,
        "rank_emoji": rank_emoji,
        "back_url": back_url,
        "back_label": back_label,
    })
