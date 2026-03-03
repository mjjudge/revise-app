"""Shared Jinja2 template environment with tier/pantheon globals."""

from fastapi.templating import Jinja2Templates

from app.services.tiers import (
    get_tier, get_next_tier, tier_progress, TIERS,
    PANTHEONS, pantheon_tiers, get_pantheon, completed_pantheons,
)


def create_templates(directory: str = "app/templates/html") -> Jinja2Templates:
    """Create a Jinja2Templates instance with tier helpers available globally."""
    tpl = Jinja2Templates(directory=directory)
    tpl.env.globals["get_tier"] = get_tier
    tpl.env.globals["get_next_tier"] = get_next_tier
    tpl.env.globals["tier_progress"] = tier_progress
    tpl.env.globals["all_tiers"] = TIERS
    tpl.env.globals["PANTHEONS"] = PANTHEONS
    tpl.env.globals["pantheon_tiers"] = pantheon_tiers
    tpl.env.globals["get_pantheon"] = get_pantheon
    tpl.env.globals["completed_pantheons"] = completed_pantheons
    return tpl
