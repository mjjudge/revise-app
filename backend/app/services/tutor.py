"""Tutor service — OpenAI-powered explanations, hints, and fun rewrites.

All prompts follow strict safety rules:
  - Age-appropriate language (KS3, ages 11-14)
  - No personal data sent to OpenAI
  - Hints must NOT reveal the answer (hints 1-2); hint 3 may be very close
  - Never reference or reproduce copyrighted book content
  - Answers are NEVER computed by OpenAI — only explanations/hints

Logging: every API call is logged with prompt + response for review.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI client (lazy singleton)
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    """Return an OpenAI client, creating it lazily."""
    global _client
    if _client is None:
        from openai import OpenAI

        api_key = settings.openai_api_key
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Configure it in .env to use tutor features."
            )
        _client = OpenAI(api_key=api_key)
    return _client


MODEL = "gpt-4o"

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM_BASE = """\
You are a friendly maths tutor for a Year 8 student (age 12-13) in the UK.
Your name is Professor Quill.
Rules you MUST follow:
1. Use simple, encouraging, age-appropriate language.
2. NEVER reveal the exact final answer — guide the student towards it.
3. NEVER reference any textbook, ISBN, publisher, or copyrighted material.
4. NEVER ask for or mention the student's real name, school, or personal details.
5. Keep responses concise — max 3-4 short sentences per hint, max 6 sentences for explanations.
6. Use British English spelling (colour, metres, etc.).
7. You may use simple maths notation but avoid LaTeX.
8. Be encouraging even when the student gets it wrong.
"""

_HINT_SYSTEM = _SYSTEM_BASE + """\
You are providing a HINT for a maths question. The student has NOT answered yet.
The hint level tells you how much help to give:
- Level 1 (nudge): Give a gentle nudge about the METHOD to use (e.g. "Think about what operation you need..."). Do NOT give any numbers from the working.
- Level 2 (worked step): Show the FIRST step of the working (e.g. "First, add up all the numbers: 3 + 7 + ..."). Still do NOT reveal the final answer.
- Level 3 (nearly there): Walk through most of the working, stopping just before the final answer. The student should be able to finish the last step themselves.
"""

_EXPLAIN_SYSTEM = _SYSTEM_BASE + """\
You are explaining WHY a student got a maths question wrong.
You are given:
- The question
- The correct answer
- The student's wrong answer
- The solution steps

Explain what likely went wrong in their reasoning, then show the correct method briefly.
Be kind — mistakes are how we learn!
You MAY reveal the correct answer since the student has already seen it.
"""

_FUN_REWRITE_SYSTEM = """\
You are a creative writer who makes maths questions fun for a 12-year-old.
Rewrite the given maths question in a fun, adventurous tone (e.g. involving dragons, quests, treasure).
Rules:
1. Keep the EXACT same mathematical content — same numbers, same operation, same answer.
2. Just change the story/framing to be more fun.
3. Keep it SHORT — one or two sentences max.
4. Use British English.
5. Do NOT change any numbers or the mathematical task.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_hint(
    question_text: str,
    skill: str,
    solution_steps: list[str],
    hint_number: int,
    params_summary: str = "",
) -> str:
    """Generate a progressive hint for the given question.

    hint_number: 1 = nudge, 2 = worked step, 3 = nearly-the-answer.
    """
    if hint_number < 1 or hint_number > 3:
        raise ValueError(f"hint_number must be 1-3, got {hint_number}")

    user_msg = (
        f"Question: {question_text}\n"
        f"Skill: {skill}\n"
        f"Solution steps: {'; '.join(solution_steps)}\n"
        f"Hint level: {hint_number}\n"
    )
    if params_summary:
        user_msg += f"Key values: {params_summary}\n"

    return _chat(system=_HINT_SYSTEM, user=user_msg, tag="hint")


def explain_mistake(
    question_text: str,
    correct_answer: str,
    student_answer: str,
    solution_steps: list[str],
    skill: str,
) -> str:
    """Explain why the student's answer was wrong."""
    user_msg = (
        f"Question: {question_text}\n"
        f"Skill: {skill}\n"
        f"Correct answer: {correct_answer}\n"
        f"Student's answer: {student_answer}\n"
        f"Solution steps: {'; '.join(solution_steps)}\n"
    )

    return _chat(system=_EXPLAIN_SYSTEM, user=user_msg, tag="explain")


def rewrite_prompt_fun(question_text: str) -> str:
    """Rewrite the question stem in a fun, adventurous tone."""
    user_msg = f"Rewrite this maths question in a fun tone:\n\n{question_text}"

    return _chat(system=_FUN_REWRITE_SYSTEM, user=user_msg, tag="fun_rewrite")


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _chat(system: str, user: str, tag: str) -> str:
    """Make a chat completion call and return the assistant message."""
    client = _get_client()

    logger.info("[tutor:%s] Sending request to %s", tag, MODEL)
    logger.debug("[tutor:%s] system=%s", tag, system[:200])
    logger.debug("[tutor:%s] user=%s", tag, user[:500])

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "[tutor:%s] Response received (%d chars, %s tokens)",
            tag,
            len(content),
            response.usage.total_tokens if response.usage else "?",
        )
        logger.debug("[tutor:%s] response=%s", tag, content[:500])
        return content.strip()

    except Exception as e:
        logger.error("[tutor:%s] OpenAI API error: %s", tag, e)
        return f"Sorry, Professor Quill is taking a break right now. Try again in a moment! ({type(e).__name__})"
