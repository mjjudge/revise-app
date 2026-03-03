"""Tutor API routes — hints, explanations, fun rewrites, and mini-lessons via OpenAI.

All routes return HTML fragments for HTMX partial updates.
"""

from __future__ import annotations

import json
import re
from fractions import Fraction

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.db.session import get_session
from app.models.question import QuestionInstance
from app.models.user import Role
from app.services.auth import get_current_user
from app.services.tutor import explain_mistake, generate_lesson, get_hint, rewrite_prompt_fun
from app.templates.feed_loader import get_template_by_id

router = APIRouter(prefix="/tutor", tags=["tutor"])


def _decode_json(s: str):
    """Decode JSON with Fraction support."""

    def _hook(d: dict):
        if "__fraction__" in d:
            return Fraction(d["num"], d["den"])
        return d

    return json.loads(s, object_hook=_hook)


def _answer_to_str(answer) -> str:
    """Convert a correct answer to a display string."""
    if isinstance(answer, Fraction):
        return str(answer)
    if isinstance(answer, dict):
        parts = [f"{k}: {v}" for k, v in answer.items()]
        return ", ".join(parts)
    if isinstance(answer, list):
        return ", ".join(str(x) for x in answer)
    return str(answer)


# ---------------------------------------------------------------------------
# POST /tutor/hint — progressive hint for a question
# ---------------------------------------------------------------------------

@router.post("/hint", response_class=HTMLResponse)
def tutor_hint(
    request: Request,
    question_id: int = Form(...),
    hint_number: int = Form(default=1),
    session: Session = Depends(get_session),
):
    """Return a hint HTML fragment (HTMX target)."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return HTMLResponse("<p class='text-red-400'>Not authorised.</p>", status_code=403)

    instance = session.get(QuestionInstance, question_id)
    if not instance:
        return HTMLResponse("<p class='text-red-400'>Question not found.</p>", status_code=404)

    template = get_template_by_id(instance.template_id)
    if not template:
        return HTMLResponse("<p class='text-red-400'>Template not found.</p>", status_code=404)

    # Cap at 3 hints
    hint_number = min(hint_number, 3)

    # Get solution steps from template
    solution_steps = template.solution.steps if template.solution else []

    # Build a params summary (safe — no personal data, just maths values)
    params = _decode_json(instance.payload_json)
    params_summary = _build_params_summary(params)

    # Call OpenAI
    hint_text = get_hint(
        question_text=instance.prompt_rendered,
        skill=instance.skill,
        solution_steps=solution_steps,
        hint_number=hint_number,
        params_summary=params_summary,
    )

    # Track hints used (increment if this is a new hint level)
    if hint_number > instance.hints_used:
        instance.hints_used = hint_number
        session.add(instance)
        session.commit()

    # Build response HTML
    next_hint = hint_number + 1
    can_get_more = hint_number < 3

    html = f"""
    <div class="bg-realm-purple-800/60 border border-realm-gold-500/40 rounded-xl p-4 mt-3">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-realm-gold-400 font-bold">💡 Hint {hint_number} of 3</span>
        <span class="text-xs text-realm-purple-400">(from Professor Quill)</span>
      </div>
      <p class="text-white text-sm leading-relaxed">{_escape_html(hint_text)}</p>
      <p class="text-xs text-realm-purple-400 mt-2">⚠️ Using hints halves your gold reward.</p>
    """

    if can_get_more:
        html += f"""
      <form class="mt-3" hx-post="/tutor/hint" hx-target="#hint-area" hx-swap="innerHTML">
        <input type="hidden" name="question_id" value="{question_id}">
        <input type="hidden" name="hint_number" value="{next_hint}">
        <button type="submit"
                onclick="setTimeout(function(){{ document.getElementById('hint-area').scrollIntoView({{behavior:'smooth', block:'center'}}); }}, 300)"
                class="px-4 py-2 bg-realm-purple-600 hover:bg-realm-purple-500 text-realm-gold-400
                       rounded-lg text-sm font-medium transition-colors">
          💡 Next Hint ({next_hint}/3)
        </button>
      </form>
        """

    html += "</div>"
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# POST /tutor/explain — explain a wrong answer
# ---------------------------------------------------------------------------

@router.post("/explain", response_class=HTMLResponse)
def tutor_explain(
    request: Request,
    question_id: int = Form(...),
    student_answer: str = Form(default=""),
    session: Session = Depends(get_session),
):
    """Return an explanation HTML fragment (HTMX target)."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return HTMLResponse("<p class='text-red-400'>Not authorised.</p>", status_code=403)

    instance = session.get(QuestionInstance, question_id)
    if not instance:
        return HTMLResponse("<p class='text-red-400'>Question not found.</p>", status_code=404)

    template = get_template_by_id(instance.template_id)
    if not template:
        return HTMLResponse("<p class='text-red-400'>Template not found.</p>", status_code=404)

    # Get correct answer string
    correct = _decode_json(instance.correct_json)
    correct_str = _answer_to_str(correct)

    # Solution steps
    solution_steps = template.solution.steps if template.solution else []

    # Call OpenAI
    explanation = explain_mistake(
        question_text=instance.prompt_rendered,
        correct_answer=correct_str,
        student_answer=student_answer,
        solution_steps=solution_steps,
        skill=instance.skill,
    )

    html = f"""
    <div class="bg-realm-purple-800/60 border border-blue-500/40 rounded-xl p-4 mt-4">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-blue-400 font-bold">🧙 Professor Quill explains:</span>
      </div>
      <p class="text-white text-sm leading-relaxed">{_escape_html(explanation)}</p>
    </div>
    """
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# POST /tutor/lesson — AI mini-lesson on the topic
# ---------------------------------------------------------------------------

@router.post("/lesson", response_class=HTMLResponse)
def tutor_lesson(
    request: Request,
    question_id: int = Form(...),
    session: Session = Depends(get_session),
):
    """Return a structured mini-lesson HTML fragment for the lesson modal."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return HTMLResponse("<p class='text-red-400'>Not authorised.</p>", status_code=403)

    instance = session.get(QuestionInstance, question_id)
    if not instance:
        return HTMLResponse("<p class='text-red-400'>Question not found.</p>", status_code=404)

    template = get_template_by_id(instance.template_id)
    if not template:
        return HTMLResponse("<p class='text-red-400'>Template not found.</p>", status_code=404)

    # Use cached lesson if available
    if instance.lesson_html:
        return HTMLResponse(instance.lesson_html)

    # Get solution steps from template
    solution_steps = template.solution.steps if template.solution else []

    # Build params summary
    params = _decode_json(instance.payload_json)
    params_summary = _build_params_summary(params)

    # Call OpenAI
    raw_lesson = generate_lesson(
        question_text=instance.prompt_rendered,
        skill=instance.skill,
        solution_steps=solution_steps,
        params_summary=params_summary,
    )

    # Convert markdown-ish text to HTML
    lesson_body = _lesson_to_html(raw_lesson)

    # Determine subject label
    if instance.skill.startswith("geog."):
        subject_label = "Geography"
        subject_icon = "🌍"
    else:
        subject_label = "Maths"
        subject_icon = "📐"

    # Skill label: take last two parts for readability
    skill_parts = instance.skill.split(".")
    skill_label = " › ".join(skill_parts[-2:]) if len(skill_parts) >= 2 else instance.skill

    lesson_html = f"""
    <div class="space-y-4">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs px-2 py-0.5 rounded-full bg-realm-purple-600 text-realm-purple-200">
          {subject_icon} {_escape_html(subject_label)}
        </span>
        <span class="text-xs text-realm-purple-400">{_escape_html(skill_label)}</span>
      </div>
      <div class="prose-lesson text-white text-sm leading-relaxed space-y-3">
        {lesson_body}
      </div>
      <div class="pt-2 border-t border-realm-purple-600 text-center">
        <p class="text-realm-purple-300 text-xs mb-3">No gold penalty for learning — knowledge is the real treasure!</p>
        <button onclick="closeLessonModal()"
                class="px-6 py-2 bg-realm-gold-500 hover:bg-realm-gold-400 text-realm-purple-900
                       font-bold rounded-xl transition-colors">
          ✏️ Try the Question
        </button>
      </div>
    </div>
    """

    # Cache it
    instance.lesson_html = lesson_html
    session.add(instance)
    session.commit()

    return HTMLResponse(lesson_html)


# ---------------------------------------------------------------------------
# POST /tutor/rewrite — fun rewrite of question stem
# ---------------------------------------------------------------------------

@router.post("/rewrite", response_class=HTMLResponse)
def tutor_rewrite(
    request: Request,
    question_id: int = Form(...),
    session: Session = Depends(get_session),
):
    """Return a fun-rewritten question stem (HTMX target)."""
    user = get_current_user(request, session)
    if not user or user.role != Role.kid:
        return HTMLResponse("<p class='text-red-400'>Not authorised.</p>", status_code=403)

    instance = session.get(QuestionInstance, question_id)
    if not instance:
        return HTMLResponse("<p class='text-red-400'>Question not found.</p>", status_code=404)

    # Use cached version if available
    if instance.fun_prompt:
        fun_text = instance.fun_prompt
    else:
        fun_text = rewrite_prompt_fun(instance.prompt_rendered)
        # Cache it
        instance.fun_prompt = fun_text
        session.add(instance)
        session.commit()

    html = f"""
    <div>
      <h2 class="text-xl font-bold text-white mb-2 leading-relaxed">
        ✨ {_escape_html(fun_text)}
      </h2>
      <p class="text-xs text-realm-purple-400">(Same question, just more fun!)</p>
    </div>
    """
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape_html(text: str) -> str:
    """Basic HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "<br>")
    )


def _build_params_summary(params: dict) -> str:
    """Build a concise summary of params for the hint prompt.

    Keeps only the key mathematical values, excludes metadata.
    """
    parts = []
    for key, val in params.items():
        if isinstance(val, list) and len(val) <= 15:
            parts.append(f"{key}: {val}")
        elif isinstance(val, (int, float, Fraction)):
            parts.append(f"{key}: {val}")
        elif isinstance(val, dict):
            # Include sub-values but keep it brief
            for sk, sv in val.items():
                if isinstance(sv, (int, float, str, Fraction)):
                    parts.append(f"{key}.{sk}: {sv}")
    return "; ".join(parts[:10])  # cap at 10 items


def _lesson_to_html(raw: str) -> str:
    """Convert GPT markdown-ish lesson text to styled HTML.

    Converts **bold headings**, numbered lists, and bullet points
    into semantic HTML with appropriate styling classes.
    """
    lines = raw.split("\n")
    html_parts: list[str] = []
    in_list = False  # tracking ordered/unordered list state

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>" if in_list == "ul" else "</ol>")
                in_list = False
            continue

        # Bold heading line: **Something**
        heading_match = re.match(r"^\*\*(.+?)\*\*\s*[-–—:]?\s*$", stripped)
        if heading_match:
            if in_list:
                html_parts.append("</ul>" if in_list == "ul" else "</ol>")
                in_list = False
            heading_text = _escape_html(heading_match.group(1))
            html_parts.append(
                f'<h4 class="text-realm-gold-400 font-bold text-base mt-2">{heading_text}</h4>'
            )
            continue

        # Bold heading with trailing content: **Something** — rest of text
        heading_content_match = re.match(r"^\*\*(.+?)\*\*\s*[-–—:]?\s*(.+)$", stripped)
        if heading_content_match:
            if in_list:
                html_parts.append("</ul>" if in_list == "ul" else "</ol>")
                in_list = False
            heading_text = _escape_html(heading_content_match.group(1))
            content = _inline_format(_escape_html(heading_content_match.group(2)))
            html_parts.append(
                f'<h4 class="text-realm-gold-400 font-bold text-base mt-2">{heading_text}</h4>'
            )
            html_parts.append(f'<p>{content}</p>')
            continue

        # Numbered list item: 1. text or 1) text
        num_match = re.match(r"^(\d+)[.)]\s+(.+)$", stripped)
        if num_match:
            if in_list != "ol":
                if in_list:
                    html_parts.append("</ul>")
                html_parts.append('<ol class="list-decimal list-inside space-y-1 ml-2">')
                in_list = "ol"
            item_text = _inline_format(_escape_html(num_match.group(2)))
            html_parts.append(f"<li>{item_text}</li>")
            continue

        # Bullet list item: - text or * text
        bullet_match = re.match(r"^[-*•]\s+(.+)$", stripped)
        if bullet_match:
            if in_list != "ul":
                if in_list:
                    html_parts.append("</ol>")
                html_parts.append('<ul class="list-disc list-inside space-y-1 ml-2">')
                in_list = "ul"
            item_text = _inline_format(_escape_html(bullet_match.group(1)))
            html_parts.append(f"<li>{item_text}</li>")
            continue

        # Regular paragraph
        if in_list:
            html_parts.append("</ul>" if in_list == "ul" else "</ol>")
            in_list = False
        content = _inline_format(_escape_html(stripped))
        html_parts.append(f"<p>{content}</p>")

    if in_list:
        html_parts.append("</ul>" if in_list == "ul" else "</ol>")

    return "\n".join(html_parts)


def _inline_format(text: str) -> str:
    """Apply inline markdown formatting (**bold**, *italic*) to escaped HTML."""
    # Bold: **text**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong class="text-realm-gold-300">\1</strong>',
        text,
    )
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text
