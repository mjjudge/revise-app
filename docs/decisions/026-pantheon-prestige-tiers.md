# ADR 026 — Pantheon Prestige Tier System

**Status:** Accepted  
**Date:** 2025-07-01

## Context

The original tier system had 9 Greek mythology tiers capping at "Heir of Olympus" (4,000 XP). Anna is approaching this cap, and we need extended progression to keep her motivated.

## Decision

Implement a **Pantheon Prestige** system: three mythological pantheons (Greek → Norse → Egyptian), each containing 9 tiers with escalating XP requirements. Total XP is cumulative (no reset).

### Pantheons

| Pantheon | Ranks | XP Range | Theme |
|----------|-------|----------|-------|
| Greek    | 0–8   | 0 – 4,000 | Purple/gold, warm classical |
| Norse    | 9–17  | 4,500 – 27,000 | Icy blues, steel, aurora |
| Egyptian | 18–26 | 32,500 – 102,000 | Gold, amber, lapis lazuli |

### Key Design Choices

1. **Cumulative XP** — no prestige reset. Players never lose progress.
2. **Escalating gaps** — XP between tiers grows per pantheon. Norse gaps: 500–5,000. Egyptian gaps: 5,500–12,000.
3. **Small inter-pantheon gaps** — 500 XP gap between Greek cap (4,000) and Norse start (4,500), giving a visible "between pantheons" window.
4. **Locked tier names** — tiers in unstarted pantheons show "???" in the journey UI.
5. **Pantheon badges** — completed pantheons earn badges (⚜️ Olympian, ⚡ Asgardian, ☥ Immortal).
6. **Pantheon-up celebration** — special banner when crossing into a new pantheon, separate from tier-up.

### Data Model Changes

- `Tier` dataclass gains `pantheon: str` field (default `"greek"`).
- New `Pantheon` frozen dataclass: `key`, `name`, `icon`, `badge`, `first_rank`, `last_rank`.
- New `PANTHEONS` list.
- New helpers: `get_pantheon()`, `completed_pantheons()`, `pantheon_tiers()`, `detect_pantheon_up()`, `get_pantheon_for_tier()`.
- `tier_progress()` now returns `pantheon` and `completed_pantheons` keys.

### UI Changes

- Tier badge in navbar shows pantheon icon + tier icon + title.
- "Your Journey" section groups tiers by pantheon with headers, completion badges, and locked state.
- Quest result page shows "New Pantheon Unlocked" celebration banner.
- Max-rank message updated to reference all three pantheons.

## Consequences

- 27 tiers provides months of progression at typical play rates (~300 XP/day).
- System is extensible: adding a 4th pantheon (e.g. Aztec, Japanese) requires only appending to `TIERS`, `PANTHEONS`, and adjusting `last_rank`.
- No DB schema changes needed — XP is still a simple integer.
- 56 tier tests (up from 26).
