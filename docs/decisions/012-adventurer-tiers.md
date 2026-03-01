# ADR 012 — Adventurer Tier System (Greek Mythology)

| Field   | Value                        |
|---------|------------------------------|
| Status  | Accepted                     |
| Date    | 2026-03-01                   |
| Epic    | 6.7                         |

## Context

XP and Gold provide numerical feedback, but Anna needs a visual, emotional
sense of progression — a feeling that she is *becoming* something as she
studies.  A tiered adventurer rank system gives named milestones, themed
colours, and a roadmap to aspire to.

## Decision

### Tier Definitions

9 tiers inspired by Greek mythology, with ascending XP thresholds:

| Rank | Title                   | Icon | XP Required |
|:----:|-------------------------|:----:|:-----------:|
| 0    | Mortal                  | 🏛️  | 0           |
| 1    | Acolyte of Athena       | 🦉  | 100         |
| 2    | Messenger of Hermes     | ⚡  | 300         |
| 3    | Warrior of Ares         | ⚔️  | 600         |
| 4    | Artisan of Hephaestus   | 🔨  | 1,000       |
| 5    | Hunter of Artemis       | 🏹  | 1,500       |
| 6    | Champion of Apollo      | ☀️  | 2,200       |
| 7    | Favoured of Poseidon    | 🔱  | 3,000       |
| 8    | Heir of Olympus         | ⚜️  | 4,000       |

Thresholds are spaced progressively wider so early tiers come quickly
(motivation) while later ones require sustained effort.

### Dynamic Theming

Each tier defines a complete colour scheme:
- `accent`: primary accent colour (used for titles, badges, XP text)
- `glow`: box-shadow colour for glowing elements
- `gradient_from/via/to`: three-stop body background gradient
- `badge_bg` / `badge_text`: tier badge pill colours

These are injected via CSS custom properties (`--tier-accent`, `--tier-glow`,
etc.) on the `<body>` element based on `user.xp`.  Utility classes
(`.tier-accent`, `.tier-badge`, `.tier-glow`, `.tier-progress-bar`) consume
these properties.

The entire page colour shifts as Anna progresses:
- Mortal: soft purple (familiar starting theme)
- Athena: blue/silver (wisdom)
- Hermes: green/gold (speed)
- Ares: deep red/bronze (intensity)
- Hephaestus: orange/copper (craft)
- Artemis: teal/emerald (nature)
- Apollo: gold/white (radiance)
- Poseidon: ocean blue (power)
- Olympus: mythical purple/pink (transcendence)

### Implementation

- **`services/tiers.py`**: Pure functional module with `get_tier()`,
  `get_next_tier()`, `tier_progress()`, `detect_tier_up()`.  All functions
  are deterministic (XP in → tier out), no DB dependency.

- **`templates/shared.py`**: Factory function `create_templates()` that
  creates Jinja2Templates instances with tier helpers registered as globals.
  Used by both `pages.py` and `quest.py`.

- **`base.html`**: Body tag uses inline style with tier gradient and CSS
  custom properties.  Falls back to default purple when no user is set.

- **All navbars**: Show tier badge pill with icon + title alongside XP/Gold.

- **`home.html`**: Full tier progress card with:
  - Current tier icon, title, flavour text
  - Progress bar toward next tier (XP into tier / XP needed, percentage)
  - Visual roadmap showing all 9 tiers (achieved = coloured, future = greyed)

- **`quest_result.html`**: Tier-up celebration banner when a tier boundary is
  crossed — icon bounce animation, "New Title Unlocked" text, tier-coloured
  glow.

### Tier-Up Detection

`detect_tier_up(old_xp, new_xp)` compares tier rank before and after XP gain.
Called in `quest_answer()` alongside existing `detect_milestone()`.  Both can
fire on the same answer (milestone every 100 XP, tier-ups at specific
thresholds).

## Consequences

- Page colours change dynamically without any CSS file changes or rebuilds
- Adding new tiers is a single entry in the `TIERS` list
- Tier logic is testable in isolation (28 tests)
- Minor overhead: one list scan per page render (9 items, negligible)
- No database migration needed — tier is computed from user.xp
- Future: could persist "highest tier reached" in DB for permanent badges
