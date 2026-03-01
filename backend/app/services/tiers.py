"""Adventurer tier system — Greek mythology themed progression.

Each tier has:
  - XP threshold
  - Title (Greek mythology inspired)
  - Emoji icon
  - Theme colours (accent, glow, gradient stops)
  - A short flavour description

Pure functions — no DB or IO.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    """An adventurer tier definition."""

    rank: int          # 0-indexed
    title: str
    icon: str          # emoji
    xp_required: int   # minimum XP
    flavour: str       # short description
    # CSS colours
    accent: str        # primary accent colour
    glow: str          # glow / shadow colour (rgba)
    gradient_from: str # body gradient start
    gradient_via: str  # body gradient middle
    gradient_to: str   # body gradient end
    badge_bg: str      # badge / pill background
    badge_text: str    # badge text colour


# ── Tier definitions (ordered by xp_required ascending) ──────────────────

TIERS: list[Tier] = [
    Tier(
        rank=0, title="Mortal", icon="🏛️", xp_required=0,
        flavour="Every legend begins with a single step",
        accent="#a78bfa", glow="rgba(167,139,250,0.3)",
        gradient_from="#3b0f7a", gradient_via="#4c1d95", gradient_to="#312e81",
        badge_bg="rgba(167,139,250,0.2)", badge_text="#a78bfa",
    ),
    Tier(
        rank=1, title="Acolyte of Athena", icon="🦉", xp_required=100,
        flavour="Wisdom begins — the owl watches over you",
        accent="#60a5fa", glow="rgba(96,165,250,0.3)",
        gradient_from="#1e1b4b", gradient_via="#1e3a5f", gradient_to="#172554",
        badge_bg="rgba(96,165,250,0.2)", badge_text="#60a5fa",
    ),
    Tier(
        rank=2, title="Messenger of Hermes", icon="⚡", xp_required=300,
        flavour="Swift of mind — the winged sandals carry you",
        accent="#34d399", glow="rgba(52,211,153,0.3)",
        gradient_from="#064e3b", gradient_via="#065f46", gradient_to="#1e3a5f",
        badge_bg="rgba(52,211,153,0.2)", badge_text="#34d399",
    ),
    Tier(
        rank=3, title="Warrior of Ares", icon="⚔️", xp_required=600,
        flavour="Battle-hardened — no equation can defeat you",
        accent="#f87171", glow="rgba(248,113,113,0.3)",
        gradient_from="#450a0a", gradient_via="#7f1d1d", gradient_to="#3b0f7a",
        badge_bg="rgba(248,113,113,0.2)", badge_text="#f87171",
    ),
    Tier(
        rank=4, title="Artisan of Hephaestus", icon="🔨", xp_required=1000,
        flavour="Forged in fire — your skills are finely crafted",
        accent="#fb923c", glow="rgba(251,146,60,0.3)",
        gradient_from="#431407", gradient_via="#7c2d12", gradient_to="#451a03",
        badge_bg="rgba(251,146,60,0.2)", badge_text="#fb923c",
    ),
    Tier(
        rank=5, title="Hunter of Artemis", icon="🏹", xp_required=1500,
        flavour="Sharp-eyed and sure — the forest bows to you",
        accent="#2dd4bf", glow="rgba(45,212,191,0.3)",
        gradient_from="#042f2e", gradient_via="#134e4a", gradient_to="#1e3a5f",
        badge_bg="rgba(45,212,191,0.2)", badge_text="#2dd4bf",
    ),
    Tier(
        rank=6, title="Champion of Apollo", icon="☀️", xp_required=2200,
        flavour="Radiant brilliance — the sun itself applauds",
        accent="#fbbf24", glow="rgba(251,191,36,0.4)",
        gradient_from="#451a03", gradient_via="#78350f", gradient_to="#3b0f7a",
        badge_bg="rgba(251,191,36,0.2)", badge_text="#fbbf24",
    ),
    Tier(
        rank=7, title="Favoured of Poseidon", icon="🔱", xp_required=3000,
        flavour="The seas part before you — unstoppable force",
        accent="#38bdf8", glow="rgba(56,189,248,0.35)",
        gradient_from="#0c4a6e", gradient_via="#075985", gradient_to="#1e1b4b",
        badge_bg="rgba(56,189,248,0.2)", badge_text="#38bdf8",
    ),
    Tier(
        rank=8, title="Heir of Olympus", icon="⚜️", xp_required=4000,
        flavour="The gods themselves bow — you are legend",
        accent="#e879f9", glow="rgba(232,121,249,0.4)",
        gradient_from="#4a044e", gradient_via="#701a75", gradient_to="#3b0764",
        badge_bg="rgba(232,121,249,0.25)", badge_text="#e879f9",
    ),
]


def get_tier(xp: int) -> Tier:
    """Return the tier for a given XP total."""
    tier = TIERS[0]
    for t in TIERS:
        if xp >= t.xp_required:
            tier = t
        else:
            break
    return tier


def get_next_tier(xp: int) -> Tier | None:
    """Return the next tier above current XP, or None if max rank."""
    current = get_tier(xp)
    if current.rank + 1 < len(TIERS):
        return TIERS[current.rank + 1]
    return None


def tier_progress(xp: int) -> dict:
    """Return progress info toward next tier.

    Returns dict with:
      - current: Tier
      - next: Tier | None
      - xp_into_tier: int (XP earned beyond current tier threshold)
      - xp_needed: int (total XP span of current tier band)
      - pct: int (0-100 progress percentage)
    """
    current = get_tier(xp)
    nxt = get_next_tier(xp)
    if nxt is None:
        return {
            "current": current,
            "next": None,
            "xp_into_tier": 0,
            "xp_needed": 0,
            "pct": 100,
        }
    xp_into = xp - current.xp_required
    xp_span = nxt.xp_required - current.xp_required
    pct = min(100, int(xp_into / xp_span * 100)) if xp_span > 0 else 100
    return {
        "current": current,
        "next": nxt,
        "xp_into_tier": xp_into,
        "xp_needed": xp_span,
        "pct": pct,
    }


def detect_tier_up(old_xp: int, new_xp: int) -> Tier | None:
    """Return the new Tier if a tier boundary was crossed, else None."""
    if new_xp <= old_xp:
        return None
    old_tier = get_tier(old_xp)
    new_tier = get_tier(new_xp)
    if new_tier.rank > old_tier.rank:
        return new_tier
    return None
