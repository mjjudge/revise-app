"""Shared Jinja2 template environment with tier globals."""

from fastapi.templating import Jinja2Templates

from app.services.tiers import get_tier, get_next_tier, tier_progress, TIERS


def create_templates(directory: str = "app/templates/html") -> Jinja2Templates:
    """Create a Jinja2Templates instance with tier helpers available globally."""
    tpl = Jinja2Templates(directory=directory)
    tpl.env.globals["get_tier"] = get_tier
    tpl.env.globals["get_next_tier"] = get_next_tier
    tpl.env.globals["tier_progress"] = tier_progress
    tpl.env.globals["all_tiers"] = TIERS
    return tpl
