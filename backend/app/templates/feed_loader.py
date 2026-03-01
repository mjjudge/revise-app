"""Pydantic models for YAML feed validation + YAML loader.

Supports loading multiple subject packs (maths, geography, etc.)
from the templates directory. Legacy maths skills/templates that only
have `chapter` are auto-mapped to subject='maths' + unit derived from chapter.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Legacy maths chapter → unit mapping
_MATHS_CHAPTER_UNIT = {
    5: "data",
    6: "algebra",
    7: "calculation",
    8: "probability",
}

# Which YAML files to load (pairs of skills + templates)
_FEED_PACKS: list[tuple[str, str]] = [
    ("skills.yaml", "templates_ch5_to_ch8.yaml"),
    ("skills_geography.yaml", "templates_geography.yaml"),
]


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
    # Geography modes (validated but generators not yet implemented)
    gridref_4fig = "gridref_4fig"
    gridref_6fig = "gridref_6fig"
    bearing_3digit = "bearing_3digit"
    grid_match = "grid_match"
    label_match = "label_match"


# ---------------------------------------------------------------------------
# Skill schema
# ---------------------------------------------------------------------------

class SkillDef(BaseModel):
    code: str
    name: str
    chapter: Optional[int] = None
    subject: Optional[str] = None
    unit: Optional[str] = None

    @model_validator(mode="after")
    def derive_subject_unit(self) -> "SkillDef":
        """Auto-map legacy maths skills that only have chapter."""
        if self.subject is None and self.chapter is not None:
            self.subject = "maths"
        if self.unit is None and self.chapter is not None:
            self.unit = _MATHS_CHAPTER_UNIT.get(self.chapter)
        return self

    @field_validator("chapter")
    @classmethod
    def chapter_range(cls, v: int | None) -> int | None:
        if v is not None and v not in (5, 6, 7, 8):
            raise ValueError(f"Chapter must be 5-8 or omitted, got {v}")
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
    model_config = {"extra": "allow"}  # allow mcq, normalise, tolerance_degrees, etc.


class SolutionSpec(BaseModel):
    steps: list[str]


class AssetSpec(BaseModel):
    kind: str  # "table", "chart", "map_grid", etc.
    id: str
    model_config = {"extra": "allow"}  # allow chart_type, columns, rows, etc.


class TemplateDef(BaseModel):
    id: str
    skill: str
    difficulty: int
    type: QuestionType
    prompt: str
    parameters: dict[str, Any]
    marking: MarkingSpec
    solution: SolutionSpec
    assets: list[AssetSpec] = []
    chapter: Optional[int] = None
    subject: Optional[str] = None
    unit: Optional[str] = None
    calculator: Optional[str] = None  # "basic" or "scientific"; None = not needed
    notes: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def derive_subject_unit(self) -> "TemplateDef":
        """Auto-map legacy maths templates that only have chapter."""
        if self.subject is None and self.chapter is not None:
            self.subject = "maths"
        if self.unit is None and self.chapter is not None:
            self.unit = _MATHS_CHAPTER_UNIT.get(self.chapter)
        return self

    @field_validator("calculator")
    @classmethod
    def calculator_values(cls, v: str | None) -> str | None:
        if v is not None and v not in ("basic", "scientific"):
            raise ValueError(f"calculator must be 'basic' or 'scientific', got '{v}'")
        return v

    @field_validator("chapter")
    @classmethod
    def chapter_range(cls, v: int | None) -> int | None:
        if v is not None and v not in (5, 6, 7, 8):
            raise ValueError(f"Chapter must be 5-8 or omitted, got {v}")
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
    skill_map = {s.code: s for s in skills.skills}

    for t in templates.templates:
        if t.skill not in skill_codes:
            errors.append(f"Template '{t.id}' references unknown skill '{t.skill}'")
            continue

        sk = skill_map[t.skill]

        # Chapter consistency (legacy maths)
        if t.chapter is not None and sk.chapter is not None:
            if t.chapter != sk.chapter:
                errors.append(
                    f"Template '{t.id}' chapter {t.chapter} != "
                    f"skill '{t.skill}' chapter {sk.chapter}"
                )

        # Subject consistency
        if t.subject and sk.subject and t.subject != sk.subject:
            errors.append(
                f"Template '{t.id}' subject '{t.subject}' != "
                f"skill '{t.skill}' subject '{sk.subject}'"
            )

        # Unit consistency
        if t.unit and sk.unit and t.unit != sk.unit:
            errors.append(
                f"Template '{t.id}' unit '{t.unit}' != "
                f"skill '{t.skill}' unit '{sk.unit}'"
            )

    return errors


# ---------------------------------------------------------------------------
# YAML loader (multi-pack)
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).parent

_skills_cache: SkillsFeed | None = None
_templates_cache: TemplatesFeed | None = None


def _load_yaml(path: Path) -> dict:
    """Load a single YAML file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_skills(path: Path | None = None) -> SkillsFeed:
    """Load and validate all skill YAML files (or a single file if path given)."""
    global _skills_cache
    if _skills_cache is not None and path is None:
        return _skills_cache

    if path is not None:
        # Single file mode (for tests)
        data = _load_yaml(path)
        return SkillsFeed.model_validate(data)

    # Multi-pack: merge all skill files
    all_skills: list[dict] = []
    for skills_file, _ in _FEED_PACKS:
        p = _TEMPLATES_DIR / skills_file
        if p.exists():
            data = _load_yaml(p)
            all_skills.extend(data.get("skills", []))

    feed = SkillsFeed.model_validate({"skills": all_skills})
    _skills_cache = feed
    return feed


def load_templates(path: Path | None = None) -> TemplatesFeed:
    """Load and validate all template YAML files (or a single file if path given)."""
    global _templates_cache
    if _templates_cache is not None and path is None:
        return _templates_cache

    if path is not None:
        # Single file mode (for tests)
        data = _load_yaml(path)
        return TemplatesFeed.model_validate(data)

    # Multi-pack: merge all template files
    all_templates: list[dict] = []
    for _, templates_file in _FEED_PACKS:
        p = _TEMPLATES_DIR / templates_file
        if p.exists():
            data = _load_yaml(p)
            all_templates.extend(data.get("templates", []))

    feed = TemplatesFeed.model_validate({"templates": all_templates})
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
    """Return all templates for a given chapter (legacy maths)."""
    templates = load_templates()
    return [t for t in templates.templates if t.chapter == chapter]


def get_templates_by_subject(subject: str) -> list[TemplateDef]:
    """Return all templates for a given subject."""
    templates = load_templates()
    return [t for t in templates.templates if t.subject == subject]


def get_templates_by_unit(subject: str, unit: str) -> list[TemplateDef]:
    """Return all templates for a given subject + unit."""
    templates = load_templates()
    return [t for t in templates.templates
            if t.subject == subject and t.unit == unit]


def get_template_by_id(template_id: str) -> TemplateDef | None:
    """Find a template by its stable id."""
    templates = load_templates()
    for t in templates.templates:
        if t.id == template_id:
            return t
    return None


def get_subjects() -> list[str]:
    """Return sorted list of distinct subjects across all loaded skills."""
    skills = load_skills()
    return sorted({s.subject for s in skills.skills if s.subject})


def get_units_for_subject(subject: str) -> list[str]:
    """Return sorted list of units for a subject."""
    skills = load_skills()
    return sorted({s.unit for s in skills.skills
                   if s.subject == subject and s.unit})


def clear_cache() -> None:
    """Clear the cached feeds (useful for tests)."""
    global _skills_cache, _templates_cache
    _skills_cache = None
    _templates_cache = None
