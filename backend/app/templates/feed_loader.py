"""Pydantic models for YAML feed validation + YAML loader."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class QuestionType(str, Enum):
    numeric = "numeric"
    multi_choice = "multi_choice"
    short_text = "short_text"
    order_list = "order_list"
    grid_fill = "grid_fill"


class MarkingMode(str, Enum):
    exact_numeric = "exact_numeric"
    exact_text_normalised = "exact_text_normalised"
    numeric_tolerance = "numeric_tolerance"
    rounding_dp = "rounding_dp"
    fraction_or_decimal = "fraction_or_decimal"
    remainder_form = "remainder_form"
    algebra_normal_form = "algebra_normal_form"
    order_match = "order_match"
    mcq = "mcq"


# ---------------------------------------------------------------------------
# Skill schema
# ---------------------------------------------------------------------------

class SkillDef(BaseModel):
    code: str
    chapter: int
    name: str

    @field_validator("chapter")
    @classmethod
    def chapter_range(cls, v: int) -> int:
        if v not in (5, 6, 7, 8):
            raise ValueError(f"Chapter must be 5-8, got {v}")
        return v

    @field_validator("code")
    @classmethod
    def code_format(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_.]+$", v):
            raise ValueError(f"Skill code must be dotted lowercase, got '{v}'")
        return v


class SkillsFeed(BaseModel):
    skills: list[SkillDef]

    @model_validator(mode="after")
    def unique_codes(self) -> "SkillsFeed":
        codes = [s.code for s in self.skills]
        dupes = [c for c in codes if codes.count(c) > 1]
        if dupes:
            raise ValueError(f"Duplicate skill codes: {set(dupes)}")
        return self


# ---------------------------------------------------------------------------
# Template schema
# ---------------------------------------------------------------------------

class MarkingSpec(BaseModel):
    mode: MarkingMode
    tolerance: Optional[float] = None
    unit_required: Optional[bool] = None
    units: Optional[str] = None
    dp_from_param: Optional[str] = None
    variable: Optional[str] = None
    accepted_forms: Optional[list[str]] = None
    rounding: Optional[dict[str, Any]] = None


class SolutionSpec(BaseModel):
    steps: list[str]


class AssetSpec(BaseModel):
    kind: str  # "table" or "chart"
    id: str
    model_config = {"extra": "allow"}  # allow chart_type, columns, rows, etc.


class TemplateDef(BaseModel):
    id: str
    chapter: int
    skill: str
    difficulty: int
    type: QuestionType
    prompt: str
    parameters: dict[str, Any]
    marking: MarkingSpec
    solution: SolutionSpec
    assets: list[AssetSpec] = []
    notes: Optional[dict[str, Any]] = None

    @field_validator("chapter")
    @classmethod
    def chapter_range(cls, v: int) -> int:
        if v not in (5, 6, 7, 8):
            raise ValueError(f"Chapter must be 5-8, got {v}")
        return v

    @field_validator("difficulty")
    @classmethod
    def difficulty_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError(f"Difficulty must be 1-5, got {v}")
        return v


class TemplatesFeed(BaseModel):
    templates: list[TemplateDef]

    @model_validator(mode="after")
    def unique_ids(self) -> "TemplatesFeed":
        ids = [t.id for t in self.templates]
        dupes = [i for i in ids if ids.count(i) > 1]
        if dupes:
            raise ValueError(f"Duplicate template ids: {set(dupes)}")
        return self


# ---------------------------------------------------------------------------
# Cross-feed validation
# ---------------------------------------------------------------------------

def validate_feeds(skills: SkillsFeed, templates: TemplatesFeed) -> list[str]:
    """
    Validate templates against skills. Returns list of error strings (empty = OK).
    """
    errors: list[str] = []
    skill_codes = {s.code for s in skills.skills}
    skill_chapters = {s.code: s.chapter for s in skills.skills}

    for t in templates.templates:
        if t.skill not in skill_codes:
            errors.append(f"Template '{t.id}' references unknown skill '{t.skill}'")
        elif t.chapter != skill_chapters[t.skill]:
            errors.append(
                f"Template '{t.id}' chapter {t.chapter} != "
                f"skill '{t.skill}' chapter {skill_chapters[t.skill]}"
            )
    return errors


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).parent

_skills_cache: SkillsFeed | None = None
_templates_cache: TemplatesFeed | None = None


def load_skills(path: Path | None = None) -> SkillsFeed:
    """Load and validate skills.yaml."""
    global _skills_cache
    if _skills_cache is not None and path is None:
        return _skills_cache
    p = path or (_TEMPLATES_DIR / "skills.yaml")
    with open(p) as f:
        data = yaml.safe_load(f)
    feed = SkillsFeed.model_validate(data)
    if path is None:
        _skills_cache = feed
    return feed


def load_templates(path: Path | None = None) -> TemplatesFeed:
    """Load and validate templates YAML."""
    global _templates_cache
    if _templates_cache is not None and path is None:
        return _templates_cache
    p = path or (_TEMPLATES_DIR / "templates_ch5_to_ch8.yaml")
    with open(p) as f:
        data = yaml.safe_load(f)
    feed = TemplatesFeed.model_validate(data)
    if path is None:
        _templates_cache = feed
    return feed


def load_and_validate(
    skills_path: Path | None = None,
    templates_path: Path | None = None,
) -> tuple[SkillsFeed, TemplatesFeed]:
    """Load both feeds and cross-validate. Raises ValueError on errors."""
    skills = load_skills(skills_path)
    templates = load_templates(templates_path)
    errors = validate_feeds(skills, templates)
    if errors:
        raise ValueError(f"Feed validation errors:\n" + "\n".join(errors))
    return skills, templates


def get_skill_map() -> dict[str, SkillDef]:
    """Return skill code -> SkillDef mapping."""
    skills = load_skills()
    return {s.code: s for s in skills.skills}


def get_templates_by_skill(skill_code: str) -> list[TemplateDef]:
    """Return all templates for a given skill code."""
    templates = load_templates()
    return [t for t in templates.templates if t.skill == skill_code]


def get_templates_by_chapter(chapter: int) -> list[TemplateDef]:
    """Return all templates for a given chapter."""
    templates = load_templates()
    return [t for t in templates.templates if t.chapter == chapter]


def get_template_by_id(template_id: str) -> TemplateDef | None:
    """Find a template by its stable id."""
    templates = load_templates()
    for t in templates.templates:
        if t.id == template_id:
            return t
    return None
