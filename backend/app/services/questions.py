"""Question generation & answer-checking service.

Orchestrates: template selection → parameter generation → prompt rendering
→ answer-key computation → persistence → marking.
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, Optional

from sqlmodel import Session, select

from app.models.question import Attempt, QuestionInstance, UserSkillProgress, SubjectProgress
from app.models.quest import QuestSession
from app.models.user import User
from app.services.generators import generate_param
from app.services.marking import MarkResult, mark
from app.services.assets import render_assets
from app.templates.feed_loader import (
    get_templates_by_chapter,
    get_templates_by_skill,
    get_templates_by_unit,
    get_template_by_id,
    TemplateDef,
)
from app.core.config import settings


# ---------------------------------------------------------------------------
# XP / Gold reward tables
# ---------------------------------------------------------------------------

_XP_TABLE = {1: 5, 2: 10, 3: 15, 4: 25, 5: 40}
_GOLD_FIRST_TRY = {1: 1, 2: 2, 3: 3, 4: 5, 5: 8}

# Milestone interval (XP)
MILESTONE_INTERVAL = 100

# Messages rotate by milestone tier
_MILESTONE_MESSAGES = [
    ("🎆 Century Club!", "You just smashed {xp} XP! Time for a reward…"),
    ("🌟 Star Power!", "{xp} XP — you're on fire!"),
    ("🏰 Castle Conquered!", "{xp} XP — nothing can stop you!"),
    ("🐉 Dragon Slayer!", "{xp} XP — legendary adventurer!"),
    ("🔮 Arcane Master!", "{xp} XP — the realm bows before you!"),
    ("⚡ Thunder Strike!", "{xp} XP — electrifying brilliance!"),
]


def detect_milestone(old_xp: int, new_xp: int, interval: int = MILESTONE_INTERVAL) -> int | None:
    """Return the milestone XP value if a boundary was crossed, else None.

    Example: old_xp=90, new_xp=115, interval=100 → returns 100
    """
    if new_xp <= old_xp:
        return None
    old_bucket = old_xp // interval
    new_bucket = new_xp // interval
    if new_bucket > old_bucket:
        return new_bucket * interval
    return None


def milestone_message(xp: int) -> tuple[str, str]:
    """Return (title, body) for a milestone, cycling through messages."""
    idx = (xp // MILESTONE_INTERVAL - 1) % len(_MILESTONE_MESSAGES)
    title, body = _MILESTONE_MESSAGES[idx]
    return title, body.format(xp=xp)


# ---------------------------------------------------------------------------
# Parameter generation
# ---------------------------------------------------------------------------

def _generate_params(template: TemplateDef, seed: int) -> dict[str, Any]:
    """Generate all parameters for a template using a seeded RNG."""
    rng = random.Random(seed)
    params: dict[str, Any] = {}

    for name, spec in template.parameters.items():
        if not isinstance(spec, dict):
            params[name] = spec
            continue
        params[name] = generate_param(rng, spec, params)

    return params


# ---------------------------------------------------------------------------
# Answer-key computation
# ---------------------------------------------------------------------------

def _compute_answer(template: TemplateDef, params: dict[str, Any]) -> Any:
    """Deterministically compute the correct answer from params + template."""
    mode = template.marking.mode

    if mode == "exact_numeric":
        return _compute_numeric(template, params)
    elif mode == "exact_text_normalised":
        return _compute_text(template, params)
    elif mode == "numeric_tolerance":
        return _compute_numeric(template, params)
    elif mode == "rounding_dp":
        return _compute_rounding(template, params)
    elif mode == "fraction_or_decimal":
        return _compute_fraction(template, params)
    elif mode == "remainder_form":
        return _compute_remainder(template, params)
    elif mode == "algebra_normal_form":
        return _compute_algebra(template, params)
    elif mode == "order_match":
        return _compute_order(template, params)
    elif mode == "mcq":
        return _compute_mcq(template, params)
    # ── Geography modes ──────────────────────────────
    elif mode in ("grid_match", "label_match"):
        return _compute_grid_match(template, params)
    elif mode == "gridref_4fig":
        return _compute_gridref(template, params, digits=4)
    elif mode == "gridref_6fig":
        return _compute_gridref(template, params, digits=6)
    elif mode == "bearing_3digit":
        return _compute_bearing(template, params)
    elif mode == "keyword_any":
        return _compute_keyword_any(template, params)
    else:
        raise ValueError(f"No answer computation for mode: {mode}")


def _compute_numeric(template: TemplateDef, params: dict[str, Any]) -> float:
    """Compute numeric answers from parameterised data."""
    skill = template.skill

    if "mean" in skill:
        values = params.get("values", [])
        return sum(values) / len(values) if values else 0

    if "median" in skill:
        values = sorted(params.get("values", []))
        n = len(values)
        if n % 2 == 1:
            return float(values[n // 2])
        return (values[n // 2 - 1] + values[n // 2]) / 2.0

    if "pie_chart" in skill:
        cats = params.get("categories", {})
        target = params.get("target_label", "")
        labels = cats.get("labels", [])
        counts = cats.get("counts", [])
        total = cats.get("total", sum(counts))
        idx = labels.index(target) if target in labels else 0
        return (counts[idx] / total) * 360

    if "substitution" in skill:
        expr = params.get("expr", {})
        assignments = params.get("assignments", {})
        coeffs = expr.get("coeffs", {})
        const = expr.get("const", 0)
        result = const
        for var, coeff in coeffs.items():
            result += coeff * assignments.get(var, 0)
        return float(result)

    if "bidmas" in skill:
        expr = params.get("expr", {})
        return float(expr.get("result", 0))

    if "metric" in skill or "convert" in skill:
        conv = params.get("conversion", {})
        value = params.get("value", 0)
        factor = conv.get("factor", 1)
        return value * factor

    # ── Geography numeric ────────────────────────────
    if "scale_distance" in skill or "scale_map_distance" in skill:
        scale = params.get("scale", {})
        ratio = scale.get("ratio", 50000)
        if "scale_map_distance" in skill:
            # Real km → map cm
            real_km = float(params.get("real_km", 0))
            return round(real_km * 100_000 / ratio, 2)
        else:
            # Map cm → real km
            map_cm = float(params.get("map_cm", 0))
            return round(map_cm * ratio / 100_000, 2)

    if "contours_height" in skill:
        point_p = params.get("point_p", {})
        return float(point_p.get("height", 0))

    if "climograph_read" in skill:
        climate = params.get("climate", {})
        rain = climate.get("rain_mm", [])
        temp = climate.get("temp_c", [])
        # Decide by prompt context: if template asks for range, compute range
        if temp and not rain:
            return float(max(temp) - min(temp))
        if rain:
            # Could be total rainfall or temp range; use template prompt
            total = sum(rain)
            t_range = float(max(temp) - min(temp)) if temp else 0
            # Heuristic: if tolerance <5 and total > 100 → total; else range
            # Actually, templates are separate IDs — distinguish by template id
            tpl_id = template.id
            if "range" in tpl_id:
                return t_range
            return float(total)
        return 0.0

    return 0.0


def _compute_text(template: TemplateDef, params: dict[str, Any]) -> str:
    # Fixed answer (map-study questions with pre-defined answers)
    if "correct_value" in params:
        return str(params["correct_value"])

    skill = template.skill
    if "mode" in skill:
        # For mode-finding: the most frequent value
        values = params.get("values", [])
        if values:
            from collections import Counter
            c = Counter(values)
            return str(c.most_common(1)[0][0])
    return ""


def _compute_rounding(template: TemplateDef, params: dict[str, Any]) -> float:
    value = params.get("value", 0.0)
    dp = params.get("dp", 2)
    return round(float(value), int(dp))


def _compute_fraction(template: TemplateDef, params: dict[str, Any]) -> Fraction:
    skill = template.skill

    if "equally_likely" in skill:
        scenario = params.get("scenario", {})
        prob = scenario.get("probability")
        if isinstance(prob, Fraction):
            return prob
        return Fraction(
            scenario.get("favourable", 1),
            scenario.get("total", 1),
        )

    if "mutually_exclusive" in skill:
        pA = params.get("pA")
        pB = params.get("pB")
        if isinstance(pA, Fraction) and isinstance(pB, Fraction):
            return pA + pB
        return Fraction(0)

    if "experimental" in skill:
        successes = params.get("successes", 0)
        trials = params.get("trials", 1)
        return Fraction(successes, trials)

    return Fraction(0)


def _compute_remainder(template: TemplateDef, params: dict[str, Any]) -> dict:
    dividend = params.get("dividend", 0)
    divisor = params.get("divisor", 1)
    q = dividend // divisor
    r = dividend % divisor
    return {"quotient": q, "remainder": r}


def _compute_algebra(template: TemplateDef, params: dict[str, Any]) -> dict:
    expr = params.get("expr", {})
    return {
        "total_coeff": expr.get("total_coeff", 0),
        "variable": template.marking.variable or "a",
    }


def _compute_order(template: TemplateDef, params: dict[str, Any]) -> list:
    events = params.get("events", {})
    return events.get("correct_order", [])


def _compute_mcq(template: TemplateDef, params: dict[str, Any]) -> str:
    distractors = params.get("distractors", {})
    return distractors.get("correct", "")


# ── Geography compute helpers ────────────────────────────

def _compute_grid_match(template: TemplateDef, params: dict[str, Any]) -> dict:
    """Extract correct_mapping from pairs parameter."""
    pairs = params.get("pairs", {})
    return pairs.get("correct_mapping", {})


def _compute_gridref(template: TemplateDef, params: dict[str, Any], *, digits: int) -> str:
    """Compute the grid reference for a named feature on the map."""
    # Fixed answer (map-study questions with pre-defined answers)
    if "correct_value" in params:
        val = params["correct_value"]
        # Preserve list for multi-answer 6-fig refs
        if isinstance(val, list):
            return val
        return str(val)

    map_data = params.get("map", {})
    feature_name = params.get("feature_name", "")

    if digits == 4:
        refs = map_data.get("grid_ref_4fig", {})
    else:
        refs = map_data.get("grid_ref_6fig", {})

    return refs.get(feature_name, "0000")


def _compute_bearing(template: TemplateDef, params: dict[str, Any]) -> int:
    """Compute the bearing from one feature to another on the map."""
    # Fixed answer (map-study questions with pre-defined answers)
    if "correct_value" in params:
        return int(params["correct_value"])

    import math as _math

    map_data = params.get("map", {})
    from_name = params.get("from_feature", "")
    to_name = params.get("to_feature", "")

    features = {f["name"]: f for f in map_data.get("features", [])}
    f_from = features.get(from_name, {})
    f_to = features.get(to_name, {})

    dx = f_to.get("x", 0) - f_from.get("x", 0)
    dy = f_to.get("y", 0) - f_from.get("y", 0)

    angle = _math.degrees(_math.atan2(dx, dy))  # atan2(east, north)
    bearing = int(round(angle % 360))
    return bearing


def _compute_keyword_any(template: TemplateDef, params: dict[str, Any]) -> Any:
    """Return the correct value for a keyword_any question."""
    cv = params.get("correct_value")
    if isinstance(cv, list):
        return cv
    return str(cv) if cv is not None else ""


def get_mcq_options(instance: QuestionInstance) -> list[str] | None:
    """Return shuffled MCQ options for a question, or None if not MCQ.

    Uses the question's seed for deterministic shuffle so options stay
    stable across page reloads.
    """
    tpl = get_template_by_id(instance.template_id)
    if not tpl or tpl.marking.mode != "mcq":
        return None
    payload = json.loads(instance.payload_json)
    dist = payload.get("distractors", {})
    correct = dist.get("correct", "")
    options = [correct] + list(dist.get("distractors", []))
    rng = random.Random(instance.seed)
    rng.shuffle(options)
    return options


def get_order_items(instance: QuestionInstance) -> list[str] | None:
    """Return shuffled items for an order_match question, or None if not applicable.

    Uses the question's seed for deterministic shuffle so items stay
    stable across page reloads.
    """
    tpl = get_template_by_id(instance.template_id)
    if not tpl or tpl.marking.mode != "order_match":
        return None
    payload = json.loads(instance.payload_json)
    events = payload.get("events", {})
    items = list(events.get("events", []))
    rng = random.Random(instance.seed)
    rng.shuffle(items)
    return items


def get_grid_fill_data(instance: QuestionInstance) -> dict | None:
    """Return data for a grid_fill question, or None if not applicable.

    Returns {left: [str], right_shuffled: [str]} where right is shuffled
    deterministically using the question seed.
    """
    tpl = get_template_by_id(instance.template_id)
    if not tpl or tpl.marking.mode not in ("grid_match", "label_match"):
        return None
    payload = json.loads(instance.payload_json)
    pairs = payload.get("pairs", {})
    left = pairs.get("left", [])
    right = list(pairs.get("right", []))

    rng = random.Random(instance.seed)
    rng.shuffle(right)

    return {"left": left, "right_shuffled": right}


# ---------------------------------------------------------------------------
# JSON encoder for Fraction and other types
# ---------------------------------------------------------------------------

class _AppEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Fraction):
            return {"__fraction__": True, "num": obj.numerator, "den": obj.denominator}
        return super().default(obj)


def _decode_fraction(d: dict) -> Any:
    if "__fraction__" in d:
        return Fraction(d["num"], d["den"])
    return d


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=_AppEncoder)


def _json_loads(s: str) -> Any:
    return json.loads(s, object_hook=_decode_fraction)


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------

def _render_prompt(template: TemplateDef, params: dict[str, Any]) -> str:
    """Simple string format of the prompt using generated params.

    Handles nested fields like {conversion.from_unit} and list formatting.
    """
    prompt = template.prompt

    # Build a flat dict for .format_map
    flat: dict[str, str] = {}
    # Also track nested dicts so {scenario.context} attribute access works
    _nested: dict[str, dict] = {}
    for key, val in params.items():
        if isinstance(val, dict):
            _nested[key] = val
            for subkey, subval in val.items():
                flat[f"{key}.{subkey}"] = str(subval)
                flat[subkey] = str(subval)  # also allow bare name
            flat[key] = str(val)
        elif isinstance(val, list):
            flat[key] = ", ".join(str(v) for v in val)
        elif isinstance(val, Fraction):
            flat[key] = str(val)
        else:
            flat[key] = str(val)

    # Namespace wrapper so {scenario.context} works with format_map
    class _Namespace:
        """Allows attribute access on a dict for str.format_map."""
        _DISPLAY_KEYS = ("expr_str", "text", "context", "title", "value")

        def __init__(self, d: dict):
            self.__dict__.update({k: str(v) for k, v in d.items()})

        def __str__(self):
            # Prefer a human-friendly display key
            for k in self._DISPLAY_KEYS:
                if k in self.__dict__:
                    return self.__dict__[k]
            return str({k: v for k, v in self.__dict__.items()})

        def __format__(self, format_spec):
            return format(str(self), format_spec)

    # Use a safe formatter that leaves unknown placeholders
    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    # Inject namespace objects for nested dicts
    safe = _SafeDict(flat)
    for key, d in _nested.items():
        safe[key] = _Namespace(d)

    try:
        rendered = prompt.format_map(safe)
    except (KeyError, ValueError, AttributeError):
        rendered = prompt  # fallback to raw prompt

    return rendered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_question(
    db: Session,
    user: User,
    *,
    skill: str | None = None,
    chapter: int | None = None,
    subject: str | None = None,
    unit: str | None = None,
    template_id: str | None = None,
    seed: int | None = None,
    exclude_template_ids: set[str] | None = None,
) -> QuestionInstance:
    """Generate a new question instance and persist it.

    Priority: template_id > skill > unit > chapter.
    Uses adaptive difficulty band from UserSkillProgress if available.

    *exclude_template_ids* – template ids already used in the current quest
    so we avoid showing the same question twice in a row.
    """
    # 1. Select template
    template = _select_template(
        db, user,
        skill=skill, chapter=chapter, subject=subject, unit=unit,
        template_id=template_id,
        exclude_template_ids=exclude_template_ids,
    )

    # 2. Seed
    if seed is None:
        seed = int(time.time() * 1000) & 0x7FFFFFFF

    # 3. Generate params
    params = _generate_params(template, seed)

    # 4. Compute answer
    correct = _compute_answer(template, params)

    # 5. Render prompt
    prompt_rendered = _render_prompt(template, params)

    # 6. Render assets
    asset_specs = [a.model_dump() for a in template.assets]
    rendered_assets = render_assets(asset_specs, params)
    assets_html = "\n".join(a["html"] for a in rendered_assets)

    # 7. Persist
    instance = QuestionInstance(
        template_id=template.id,
        skill=template.skill,
        chapter=template.chapter,
        difficulty=template.difficulty,
        seed=seed,
        prompt_rendered=prompt_rendered,
        payload_json=_json_dumps(params),
        correct_json=_json_dumps(correct),
        assets_html=assets_html,
        user_id=user.id,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def check_answer(
    db: Session,
    user: User,
    question_id: int,
    student_answer: str,
    *,
    quest: QuestSession | None = None,
) -> tuple[Attempt, MarkResult, bool]:
    """Mark a student's answer against the stored correct answer.

    Returns (attempt, mark_result, is_boosted).

    When quest is provided, applies streak bonuses:
      - 3+ in a row: +50% XP
      - 5+ in a row: +100% XP
    Practice Boost: 2× gold + 1.5× XP for weak skills.
    Also enforces the weekly gold cap from settings.
    """
    instance = db.get(QuestionInstance, question_id)
    if instance is None:
        raise ValueError(f"Question {question_id} not found")

    template = get_template_by_id(instance.template_id)
    if template is None:
        raise ValueError(f"Template {instance.template_id} not found")

    # Count previous attempts
    prev_count = len([a for a in instance.attempts if a.user_id == user.id])
    attempt_num = prev_count + 1

    # Decode correct answer
    correct = _json_loads(instance.correct_json)

    # Build marking spec dict from template
    marking_spec = template.marking.model_dump()

    # If dp_from_param, resolve it
    if "dp_from_param" in marking_spec and marking_spec["dp_from_param"]:
        payload = _json_loads(instance.payload_json)
        marking_spec["dp"] = payload.get(marking_spec["dp_from_param"], 2)

    # Mark
    result = mark(student_answer, correct, marking_spec)

    # Compute rewards
    xp = 0
    gold = 0
    is_boosted = False
    if result.correct:
        base_xp = _XP_TABLE.get(instance.difficulty, 10)
        if attempt_num == 1:
            xp = base_xp
            gold = _GOLD_FIRST_TRY.get(instance.difficulty, 1)
        elif attempt_num == 2:
            xp = base_xp // 2
        # 3rd+ attempt: no XP

        # Quest streak bonus (applied to XP)
        if quest and attempt_num == 1:
            quest.streak += 1
            quest.wrong_streak = 0  # reset wrong streak on correct
            if quest.streak > quest.best_streak:
                quest.best_streak = quest.streak
            if quest.streak >= 5:
                xp = int(xp * 2.0)  # +100%
            elif quest.streak >= 3:
                xp = int(xp * 1.5)  # +50%

        # Practice Boost: extra rewards for weak skills
        boosted_skills = get_boosted_skills(db, user.id)
        if instance.skill in boosted_skills:
            is_boosted = True
            gold = gold * 2        # 2× gold
            xp = int(xp * 1.5)    # 1.5× XP
    else:
        # Reset quest streak on wrong answer; increment wrong streak
        if quest:
            quest.streak = 0
            quest.wrong_streak += 1

    # Weekly gold cap enforcement
    if gold > 0:
        # Hint penalty: halve gold if any hints were used
        if instance.hints_used > 0:
            gold = gold // 2  # integer division — at least halved

        gold_this_week = _gold_earned_this_week(db, user)
        remaining = max(0, settings.weekly_gold_cap - gold_this_week)
        gold = min(gold, remaining)

    # Update user totals
    if xp > 0 or gold > 0:
        user.xp += xp
        user.gold += gold
        db.add(user)

    # Persist attempt
    attempt = Attempt(
        question_id=question_id,
        user_id=user.id,
        answer_raw=student_answer,
        is_correct=result.correct,
        score=result.score,
        xp_earned=xp,
        gold_earned=gold,
        feedback=result.feedback,
        attempt_number=attempt_num,
    )
    db.add(attempt)

    # Update skill progress
    _update_skill_progress(db, user, instance.skill, result.correct)

    # Update subject progress
    subject_code = template.subject or (quest.subject if quest else None) or "maths"
    _update_subject_progress(
        db, user, subject_code,
        xp_earned=xp,
        gold_earned=gold,
        correct=result.correct and attempt_num == 1,
        quest_finished=quest.finished if quest else False,
        streak=quest.streak if quest else 0,
    )

    db.commit()
    db.refresh(attempt)

    return attempt, result, is_boosted


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _exclude_recent(
    candidates: list[TemplateDef],
    exclude_ids: set[str],
) -> list[TemplateDef]:
    """Remove recently-used templates; fall back to full list if all excluded."""
    if not exclude_ids:
        return candidates
    filtered = [t for t in candidates if t.id not in exclude_ids]
    return filtered if filtered else candidates


def _select_template(
    db: Session,
    user: User,
    *,
    skill: str | None,
    chapter: int | None,
    subject: str | None = None,
    unit: str | None = None,
    template_id: str | None,
    exclude_template_ids: set[str] | None = None,
) -> TemplateDef:
    """Pick the right template, considering adaptive difficulty.

    *exclude_template_ids* lists templates recently shown in the current
    quest so we avoid back-to-back repeats.  If excluding leaves no
    candidates we fall back to the full pool.
    """
    if template_id:
        t = get_template_by_id(template_id)
        if t is None:
            raise ValueError(f"Template '{template_id}' not found")
        return t

    excl = exclude_template_ids or set()

    if skill:
        templates = get_templates_by_skill(skill)
        band = _get_user_band(db, user, skill)
        # Filter to templates near the user's band
        nearby = [t for t in templates if abs(t.difficulty - band) <= 1]
        if not nearby:
            nearby = templates
        nearby = _exclude_recent(nearby, excl)
        rng = random.Random()
        return rng.choice(nearby)

    if unit and subject:
        templates = get_templates_by_unit(subject, unit)
        if not templates:
            raise ValueError(f"No templates for {subject}/{unit}")
        templates = _exclude_recent(templates, excl)
        rng = random.Random()
        return rng.choice(templates)

    if chapter:
        templates = get_templates_by_chapter(chapter)
        if not templates:
            raise ValueError(f"No templates for chapter {chapter}")
        templates = _exclude_recent(templates, excl)
        rng = random.Random()
        return rng.choice(templates)

    raise ValueError("Must specify skill, chapter, unit, or template_id")


def _get_user_band(db: Session, user: User, skill: str) -> int:
    """Get user's current difficulty band for a skill (default 2)."""
    stmt = select(UserSkillProgress).where(
        UserSkillProgress.user_id == user.id,
        UserSkillProgress.skill == skill,
    )
    progress = db.exec(stmt).first()
    return progress.current_band if progress else 2


def _update_skill_progress(db: Session, user: User, skill: str, correct: bool) -> None:
    """Update adaptive difficulty tracking after an attempt."""
    stmt = select(UserSkillProgress).where(
        UserSkillProgress.user_id == user.id,
        UserSkillProgress.skill == skill,
    )
    progress = db.exec(stmt).first()
    if progress is None:
        progress = UserSkillProgress(
            user_id=user.id,
            skill=skill,
            current_band=2,
        )

    progress.attempts_total += 1
    progress.last_attempted = datetime.now(timezone.utc)

    if correct:
        progress.attempts_correct += 1
        progress.streak += 1
        # Level up after 3 consecutive correct
        if progress.streak >= 3 and progress.current_band < 5:
            progress.current_band += 1
            progress.streak = 0
    else:
        progress.streak = 0
        # Level down after getting it wrong (but not below 1)
        if progress.current_band > 1:
            progress.current_band -= 1

    db.add(progress)


def _update_subject_progress(
    db: Session,
    user: User,
    subject: str,
    *,
    xp_earned: int,
    gold_earned: int,
    correct: bool,
    quest_finished: bool,
    streak: int,
) -> None:
    """Increment denormalised per-subject stats after each answer."""
    stmt = select(SubjectProgress).where(
        SubjectProgress.user_id == user.id,
        SubjectProgress.subject == subject,
    )
    sp = db.exec(stmt).first()
    if sp is None:
        sp = SubjectProgress(user_id=user.id, subject=subject)

    sp.xp_earned += xp_earned
    sp.gold_earned += gold_earned
    sp.questions_answered += 1
    if correct:
        sp.questions_correct += 1
    if quest_finished:
        sp.quests_completed += 1
    if streak > sp.best_streak:
        sp.best_streak = streak
    sp.last_played = datetime.now(timezone.utc)

    db.add(sp)


def get_subject_progress(db: Session, user_id: int, subject: str) -> SubjectProgress | None:
    """Retrieve SubjectProgress for a user + subject, or None."""
    stmt = select(SubjectProgress).where(
        SubjectProgress.user_id == user_id,
        SubjectProgress.subject == subject,
    )
    return db.exec(stmt).first()


def get_all_subject_progress(db: Session, user_id: int) -> dict[str, SubjectProgress]:
    """Return {subject_code: SubjectProgress} for a user."""
    stmt = select(SubjectProgress).where(SubjectProgress.user_id == user_id)
    rows = db.exec(stmt).all()
    return {sp.subject: sp for sp in rows}


def get_boosted_skills(db: Session, user_id: int) -> set[str]:
    """Return skill codes qualifying for Practice Boost.

    A skill qualifies when:
    - accuracy ≤60 % AND ≥3 attempts, OR
    - current_band == 1 (adaptive system already flagged it).

    A skill is *removed* from boost once accuracy ≥75 % over ≥5 attempts.
    """
    stmt = select(UserSkillProgress).where(
        UserSkillProgress.user_id == user_id,
    )
    rows = db.exec(stmt).all()
    boosted: set[str] = set()
    for sp in rows:
        acc = (sp.attempts_correct / sp.attempts_total * 100) if sp.attempts_total else 0
        # Auto-remove: accuracy ≥75% with ≥5 attempts means mastered
        if sp.attempts_total >= 5 and acc >= 75:
            continue
        # Boost: low accuracy with enough data, or band dropped to 1
        if (sp.attempts_total >= 3 and acc <= 60) or sp.current_band == 1:
            boosted.add(sp.skill)
    return boosted


def get_skill_insights(
    db: Session, user_id: int, top_n: int = 3,
) -> dict[str, dict[str, list[dict]]]:
    """Return strongest and weakest skills per subject for the admin dashboard.

    Returns::

        {
            "maths": {
                "strongest": [{"code": "...", "name": "...", "accuracy": 100, "attempts": 9}, ...],
                "weakest":   [{"code": "...", "name": "...", "accuracy": 0, "attempts": 2}, ...],
            },
            "geography": { ... },
        }

    Only includes skills with ≥2 attempts so streaky single-attempt data
    doesn't dominate.  Strongest = highest accuracy, weakest = lowest.
    """
    from app.templates.feed_loader import get_skill_map

    skill_map = get_skill_map()

    # Fetch all skill progress rows for this user
    stmt = select(UserSkillProgress).where(
        UserSkillProgress.user_id == user_id,
        UserSkillProgress.attempts_total >= 2,
    )
    rows = db.exec(stmt).all()

    # Bucket by subject
    by_subject: dict[str, list[dict]] = {}
    for sp in rows:
        sk = skill_map.get(sp.skill)
        subject = sk.subject if sk else ("maths" if not sp.skill.startswith("geog.") else "geography")
        name = sk.name if sk else sp.skill

        accuracy = int(sp.attempts_correct / sp.attempts_total * 100) if sp.attempts_total else 0
        entry = {
            "code": sp.skill,
            "name": name,
            "accuracy": accuracy,
            "attempts": sp.attempts_total,
            "band": sp.current_band,
        }
        by_subject.setdefault(subject, []).append(entry)

    result: dict[str, dict[str, list[dict]]] = {}
    for subject, entries in by_subject.items():
        # Sort by accuracy descending (ties broken by more attempts)
        sorted_entries = sorted(entries, key=lambda e: (e["accuracy"], e["attempts"]), reverse=True)
        strongest = sorted_entries[:top_n]
        # Weakest = lowest accuracy (ties broken by more attempts = more evidence)
        weakest_sorted = sorted(entries, key=lambda e: (e["accuracy"], -e["attempts"]))
        weakest = weakest_sorted[:top_n]
        result[subject] = {"strongest": strongest, "weakest": weakest}

    return result


def _gold_earned_this_week(db: Session, user: User) -> int:
    """Sum gold earned by user in the current ISO week (Mon-Sun)."""
    from sqlmodel import func

    now = datetime.now(timezone.utc)
    # Monday of current week at 00:00 UTC
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - __import__("datetime").timedelta(days=now.weekday())

    stmt = select(func.coalesce(func.sum(Attempt.gold_earned), 0)).where(
        Attempt.user_id == user.id,
        Attempt.created_at >= week_start,
    )
    result = db.exec(stmt).one()
    return int(result)
