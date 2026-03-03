"""Adventurer tier system — Pantheon prestige progression.

Three mythological pantheons, each with 9 tiers:
  1. Greek  (0 – 4 000 XP)
  2. Norse  (4 500 – 27 000 XP)
  3. Egyptian (32 500 – 102 000 XP)

Each tier has:
  - XP threshold
  - Title (mythology inspired)
  - Emoji icon
  - Pantheon key
  - Theme colours (accent, glow, gradient stops)
  - A short flavour description

Pure functions — no DB or IO.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    """An adventurer tier definition."""

    rank: int          # 0-indexed across all pantheons
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
    pantheon: str = "greek"  # "greek", "norse", or "egyptian"


@dataclass(frozen=True)
class Pantheon:
    """A mythological pantheon grouping."""

    key: str           # "greek", "norse", "egyptian"
    name: str          # display name
    icon: str          # emoji
    badge: str         # completion badge text
    first_rank: int    # first tier rank in this pantheon
    last_rank: int     # last tier rank in this pantheon


PANTHEONS: list[Pantheon] = [
    Pantheon(key="greek",    name="Greek",    icon="🏛️", badge="⚜️ Olympian",   first_rank=0,  last_rank=8),
    Pantheon(key="norse",    name="Norse",    icon="❄️", badge="⚡ Asgardian",   first_rank=9,  last_rank=17),
    Pantheon(key="egyptian", name="Egyptian", icon="🏺", badge="☥ Immortal",    first_rank=18, last_rank=26),
]


# ── Tier definitions (ordered by xp_required ascending) ──────────────────
# Greek Pantheon — ranks 0-8, XP 0 – 4 000

TIERS: list[Tier] = [
    Tier(
        rank=0, title="Mortal", icon="🏛️", xp_required=0,
        flavour="Every legend begins with a single step",
        accent="#a78bfa", glow="rgba(167,139,250,0.3)",
        gradient_from="#3b0f7a", gradient_via="#4c1d95", gradient_to="#312e81",
        badge_bg="rgba(167,139,250,0.2)", badge_text="#a78bfa",
        pantheon="greek",
    ),
    Tier(
        rank=1, title="Acolyte of Athena", icon="🦉", xp_required=100,
        flavour="Wisdom begins — the owl watches over you",
        accent="#60a5fa", glow="rgba(96,165,250,0.3)",
        gradient_from="#1e1b4b", gradient_via="#1e3a5f", gradient_to="#172554",
        badge_bg="rgba(96,165,250,0.2)", badge_text="#60a5fa",
        pantheon="greek",
    ),
    Tier(
        rank=2, title="Messenger of Hermes", icon="⚡", xp_required=300,
        flavour="Swift of mind — the winged sandals carry you",
        accent="#34d399", glow="rgba(52,211,153,0.3)",
        gradient_from="#064e3b", gradient_via="#065f46", gradient_to="#1e3a5f",
        badge_bg="rgba(52,211,153,0.2)", badge_text="#34d399",
        pantheon="greek",
    ),
    Tier(
        rank=3, title="Warrior of Ares", icon="⚔️", xp_required=600,
        flavour="Battle-hardened — no equation can defeat you",
        accent="#f87171", glow="rgba(248,113,113,0.3)",
        gradient_from="#450a0a", gradient_via="#7f1d1d", gradient_to="#3b0f7a",
        badge_bg="rgba(248,113,113,0.2)", badge_text="#f87171",
        pantheon="greek",
    ),
    Tier(
        rank=4, title="Artisan of Hephaestus", icon="🔨", xp_required=1000,
        flavour="Forged in fire — your skills are finely crafted",
        accent="#fb923c", glow="rgba(251,146,60,0.3)",
        gradient_from="#431407", gradient_via="#7c2d12", gradient_to="#451a03",
        badge_bg="rgba(251,146,60,0.2)", badge_text="#fb923c",
        pantheon="greek",
    ),
    Tier(
        rank=5, title="Hunter of Artemis", icon="🏹", xp_required=1500,
        flavour="Sharp-eyed and sure — the forest bows to you",
        accent="#2dd4bf", glow="rgba(45,212,191,0.3)",
        gradient_from="#042f2e", gradient_via="#134e4a", gradient_to="#1e3a5f",
        badge_bg="rgba(45,212,191,0.2)", badge_text="#2dd4bf",
        pantheon="greek",
    ),
    Tier(
        rank=6, title="Champion of Apollo", icon="☀️", xp_required=2200,
        flavour="Radiant brilliance — the sun itself applauds",
        accent="#fbbf24", glow="rgba(251,191,36,0.4)",
        gradient_from="#451a03", gradient_via="#78350f", gradient_to="#3b0f7a",
        badge_bg="rgba(251,191,36,0.2)", badge_text="#fbbf24",
        pantheon="greek",
    ),
    Tier(
        rank=7, title="Favoured of Poseidon", icon="🔱", xp_required=3000,
        flavour="The seas part before you — unstoppable force",
        accent="#38bdf8", glow="rgba(56,189,248,0.35)",
        gradient_from="#0c4a6e", gradient_via="#075985", gradient_to="#1e1b4b",
        badge_bg="rgba(56,189,248,0.2)", badge_text="#38bdf8",
        pantheon="greek",
    ),
    Tier(
        rank=8, title="Heir of Olympus", icon="⚜️", xp_required=4000,
        flavour="The gods themselves bow — you are legend",
        accent="#e879f9", glow="rgba(232,121,249,0.4)",
        gradient_from="#4a044e", gradient_via="#701a75", gradient_to="#3b0764",
        badge_bg="rgba(232,121,249,0.25)", badge_text="#e879f9",
        pantheon="greek",
    ),

    # ── Norse Pantheon — ranks 9-17, XP 4 500 – 27 000 ────────────────────
    Tier(
        rank=9, title="Thrall of Midgard", icon="❄️", xp_required=4_500,
        flavour="The frost calls — a new saga begins",
        accent="#93c5fd", glow="rgba(147,197,253,0.3)",
        gradient_from="#1a1f36", gradient_via="#1e293b", gradient_to="#0f172a",
        badge_bg="rgba(147,197,253,0.2)", badge_text="#93c5fd",
        pantheon="norse",
    ),
    Tier(
        rank=10, title="Skald of the Sagas", icon="📜", xp_required=5_500,
        flavour="Your deeds echo in the mead halls of Asgard",
        accent="#a5b4fc", glow="rgba(165,180,252,0.3)",
        gradient_from="#1e1b4b", gradient_via="#252660", gradient_to="#1a1f36",
        badge_bg="rgba(165,180,252,0.2)", badge_text="#a5b4fc",
        pantheon="norse",
    ),
    Tier(
        rank=11, title="Shield of Freya", icon="🛡️", xp_required=7_000,
        flavour="Blessed by the Vanir — beauty and strength entwined",
        accent="#67e8f9", glow="rgba(103,232,249,0.3)",
        gradient_from="#0c2a3e", gradient_via="#164e63", gradient_to="#0f172a",
        badge_bg="rgba(103,232,249,0.2)", badge_text="#67e8f9",
        pantheon="norse",
    ),
    Tier(
        rank=12, title="Berserker Reborn", icon="🐺", xp_required=9_000,
        flavour="Fury unleashed — the wolf spirit runs within you",
        accent="#f87171", glow="rgba(248,113,113,0.3)",
        gradient_from="#3b0a0a", gradient_via="#6b1a1a", gradient_to="#1a1f36",
        badge_bg="rgba(248,113,113,0.2)", badge_text="#f87171",
        pantheon="norse",
    ),
    Tier(
        rank=13, title="Rune Weaver", icon="🔮", xp_required=11_500,
        flavour="Ancient symbols bend to your will",
        accent="#c084fc", glow="rgba(192,132,252,0.3)",
        gradient_from="#2e1065", gradient_via="#3b0f7a", gradient_to="#1e1b4b",
        badge_bg="rgba(192,132,252,0.2)", badge_text="#c084fc",
        pantheon="norse",
    ),
    Tier(
        rank=14, title="Valkyrie's Chosen", icon="🪽", xp_required=14_500,
        flavour="Wings of light carry you above the battlefield",
        accent="#f0abfc", glow="rgba(240,171,252,0.35)",
        gradient_from="#4a044e", gradient_via="#5b1060", gradient_to="#2e1065",
        badge_bg="rgba(240,171,252,0.2)", badge_text="#f0abfc",
        pantheon="norse",
    ),
    Tier(
        rank=15, title="Einherjar Eternal", icon="⚔️", xp_required=18_000,
        flavour="Fallen and risen — an immortal warrior of Valhalla",
        accent="#fcd34d", glow="rgba(252,211,77,0.35)",
        gradient_from="#3b2506", gradient_via="#5a3a0f", gradient_to="#1a1f36",
        badge_bg="rgba(252,211,77,0.2)", badge_text="#fcd34d",
        pantheon="norse",
    ),
    Tier(
        rank=16, title="Keeper of Yggdrasil", icon="🌳", xp_required=22_000,
        flavour="The World Tree whispers its secrets to you alone",
        accent="#4ade80", glow="rgba(74,222,128,0.3)",
        gradient_from="#052e16", gradient_via="#14532d", gradient_to="#0f172a",
        badge_bg="rgba(74,222,128,0.2)", badge_text="#4ade80",
        pantheon="norse",
    ),
    Tier(
        rank=17, title="Allfather's Heir", icon="⚡", xp_required=27_000,
        flavour="Odin's wisdom and Thor's might — the nine realms are yours",
        accent="#e2e8f0", glow="rgba(226,232,240,0.4)",
        gradient_from="#1e293b", gradient_via="#334155", gradient_to="#0f172a",
        badge_bg="rgba(226,232,240,0.25)", badge_text="#e2e8f0",
        pantheon="norse",
    ),

    # ── Egyptian Pantheon — ranks 18-26, XP 32 500 – 102 000 ──────────────
    Tier(
        rank=18, title="Scribe of the Nile", icon="🪶", xp_required=32_500,
        flavour="The river of knowledge flows through your pen",
        accent="#fbbf24", glow="rgba(251,191,36,0.3)",
        gradient_from="#3d2b0f", gradient_via="#5c410e", gradient_to="#1a0f00",
        badge_bg="rgba(251,191,36,0.2)", badge_text="#fbbf24",
        pantheon="egyptian",
    ),
    Tier(
        rank=19, title="Keeper of Ma'at", icon="⚖️", xp_required=38_500,
        flavour="Truth and balance guide your every step",
        accent="#a78bfa", glow="rgba(167,139,250,0.3)",
        gradient_from="#312e81", gradient_via="#3730a3", gradient_to="#1e1b4b",
        badge_bg="rgba(167,139,250,0.2)", badge_text="#a78bfa",
        pantheon="egyptian",
    ),
    Tier(
        rank=20, title="Priest of Thoth", icon="🐦", xp_required=45_000,
        flavour="The ibis-headed god shares his infinite wisdom",
        accent="#2dd4bf", glow="rgba(45,212,191,0.3)",
        gradient_from="#042f2e", gradient_via="#115e59", gradient_to="#0f172a",
        badge_bg="rgba(45,212,191,0.2)", badge_text="#2dd4bf",
        pantheon="egyptian",
    ),
    Tier(
        rank=21, title="Guardian of Anubis", icon="⚱️", xp_required=52_000,
        flavour="The jackal watches — you stand between worlds",
        accent="#818cf8", glow="rgba(129,140,248,0.3)",
        gradient_from="#1e1b4b", gradient_via="#2d2a70", gradient_to="#0c0a3e",
        badge_bg="rgba(129,140,248,0.2)", badge_text="#818cf8",
        pantheon="egyptian",
    ),
    Tier(
        rank=22, title="Voice of Ra", icon="☀️", xp_required=60_000,
        flavour="The sun obeys your command — light eternal",
        accent="#f59e0b", glow="rgba(245,158,11,0.4)",
        gradient_from="#451a03", gradient_via="#78350f", gradient_to="#3d2b0f",
        badge_bg="rgba(245,158,11,0.2)", badge_text="#f59e0b",
        pantheon="egyptian",
    ),
    Tier(
        rank=23, title="Pharaoh's Champion", icon="👑", xp_required=69_000,
        flavour="Crowned in glory — the desert bows before you",
        accent="#f97316", glow="rgba(249,115,22,0.35)",
        gradient_from="#431407", gradient_via="#7c2d12", gradient_to="#451a03",
        badge_bg="rgba(249,115,22,0.2)", badge_text="#f97316",
        pantheon="egyptian",
    ),
    Tier(
        rank=24, title="Eye of Horus", icon="👁️", xp_required=79_000,
        flavour="All-seeing, all-knowing — nothing escapes your gaze",
        accent="#38bdf8", glow="rgba(56,189,248,0.35)",
        gradient_from="#0c4a6e", gradient_via="#075985", gradient_to="#1e1b4b",
        badge_bg="rgba(56,189,248,0.2)", badge_text="#38bdf8",
        pantheon="egyptian",
    ),
    Tier(
        rank=25, title="Avatar of Osiris", icon="🌙", xp_required=90_000,
        flavour="Death and rebirth — you transcend the mortal coil",
        accent="#4ade80", glow="rgba(74,222,128,0.3)",
        gradient_from="#052e16", gradient_via="#065f46", gradient_to="#042f2e",
        badge_bg="rgba(74,222,128,0.2)", badge_text="#4ade80",
        pantheon="egyptian",
    ),
    Tier(
        rank=26, title="Child of the Stars", icon="⭐", xp_required=102_000,
        flavour="Beyond all pantheons — you shine among the constellations",
        accent="#fde68a", glow="rgba(253,230,138,0.4)",
        gradient_from="#1e1b4b", gradient_via="#3d2b0f", gradient_to="#0f172a",
        badge_bg="rgba(253,230,138,0.25)", badge_text="#fde68a",
        pantheon="egyptian",
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
      - pantheon: Pantheon (current pantheon)
      - completed_pantheons: list[Pantheon]
    """
    current = get_tier(xp)
    nxt = get_next_tier(xp)
    pantheon = get_pantheon(xp)
    completed = completed_pantheons(xp)
    if nxt is None:
        return {
            "current": current,
            "next": None,
            "xp_into_tier": 0,
            "xp_needed": 0,
            "pct": 100,
            "pantheon": pantheon,
            "completed_pantheons": completed,
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
        "pantheon": pantheon,
        "completed_pantheons": completed,
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


# ── Pantheon helpers ─────────────────────────────────────────────────────

def get_pantheon(xp: int) -> Pantheon:
    """Return the Pantheon the user is currently in."""
    tier = get_tier(xp)
    for p in PANTHEONS:
        if p.first_rank <= tier.rank <= p.last_rank:
            return p
    return PANTHEONS[0]  # fallback


def get_pantheon_for_tier(tier: Tier) -> Pantheon:
    """Return the Pantheon a given tier belongs to."""
    for p in PANTHEONS:
        if p.key == tier.pantheon:
            return p
    return PANTHEONS[0]


def completed_pantheons(xp: int) -> list[Pantheon]:
    """Return list of Pantheons the user has fully completed."""
    tier = get_tier(xp)
    result = []
    for p in PANTHEONS:
        if tier.rank > p.last_rank:
            result.append(p)
    return result


def pantheon_tiers(pantheon_key: str) -> list[Tier]:
    """Return list of Tiers belonging to a specific pantheon."""
    return [t for t in TIERS if t.pantheon == pantheon_key]


def detect_pantheon_up(old_xp: int, new_xp: int) -> Pantheon | None:
    """Return the new Pantheon if the user crossed into a new one, else None."""
    if new_xp <= old_xp:
        return None
    old_pantheon = get_pantheon(old_xp)
    new_pantheon = get_pantheon(new_xp)
    if new_pantheon.key != old_pantheon.key:
        return new_pantheon
    return None
