# SESSION_STATE

## Current objective
EPIC 8 — Multi-subject navigation framework (Maths + Geography + History "Coming Soon").

## Completed this session
- EPIC 8 Story 8.1: Multi-subject feed loader + subject dashboard UI
  - **feed_loader.py**: Major refactor for multi-subject support:
    - `SkillDef` and `TemplateDef` now have optional `subject`, `unit` fields; `chapter` is optional
    - Auto-mapping for legacy maths: chapter 5→data, 6→algebra, 7→calculation, 8→probability
    - New `MarkingMode` values: gridref_4fig, gridref_6fig, bearing_3digit, grid_match, label_match
    - Loads multiple YAML packs: skills.yaml + templates_ch5_to_ch8.yaml AND skills_geography.yaml + templates_geography.yaml
    - New query helpers: `get_templates_by_subject()`, `get_templates_by_unit()`, `get_subjects()`, `get_units_for_subject()`, `clear_cache()`
    - Cross-validation updated for subject/unit consistency
  - **Subject dashboard**: Home page (`/`) transformed from 4 maths chapter cards to 3 subject cards (Maths=ready, Geography=Coming Soon, History=Coming Soon greyed out)
  - **Subject home page**: New `/subject/{name}` route + `subject_home.html` template showing unit cards per subject
  - **Persistent breadcrumb**: Quest chapter page now has home → subject → chapter breadcrumb in nav
  - **Tests**: Updated `test_feed_loader.py` (14 tests) and `test_quality.py` (43 tests) for multi-subject; E2E generation tests filtered to maths-only (geography generators are EPIC 9)
  - **Docs**: BACKLOG updated, ADR 015 created, QUESTION_FEED_SPEC.md fully rewritten
  - All 199 tests pass

## Previous session work
- EPICs 0-6.7 fully implemented (Docker/Caddy, auth, 30 maths templates, gamification, tutor, calculator, milestones, tiers)
- Live bug fixes: DB migration, MCQ radios, context-aware data, hint scroll, algebra prompts, pie charts, probability ordering, rounding dots, BIDMAS superscript

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic, seed-based (ADR 005)
- Asset rendering: Pure inline SVG + HTML, no matplotlib (ADR 006)
- Gamification: Quest loops, streak bonuses, gold cap, payouts (ADR 007)
- Tutor: GPT-4o, 3 hint levels, explain + fun rewrite, halve gold penalty (ADR 008)
- Quality: Structured logging, error pages, E2E tests, retry UX (ADR 009)
- Calculator: On-screen basic calculator, template-level opt-in (ADR 010)
- Milestones: Fireworks + mini Sudoku every 100 XP (ADR 011)
- Tiers: 9-tier Greek mythology progression with dynamic theming (ADR 012)
- Context-aware data: sensible UK ranges + y-axis units on charts (ADR 013)
- Hint UX: scroll-to-hint on button click for visibility (ADR 014)
- Multi-subject: feed_loader multi-pack, subject/unit navigation, new marking modes (ADR 015)

## Open questions
- None for EPIC 8.1

## Next actions (EPIC 8 continued + EPIC 9)
- [ ] EPIC 8.2: Subject-scoped progress tracking (per-subject XP/stats)
- [ ] EPIC 9: Geography generators + renderers (map_grid, compass_rose, contour assets)
- [ ] EPIC 10: History subject pack (YAML templates + generators)
- [ ] EPIC 11: Cross-subject features (combined leaderboard, subject streaks)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth

## Notes / gotchas
- Geography YAML files exist but generators are NOT implemented yet (EPIC 9 work)
- E2E quality tests correctly filter to maths-only to avoid geography generator failures
- feed_loader cache must be cleared between tests (autouse fixture handles this)
- Maths chapter routes (`/quest/chapter/{N}`) remain fully backward-compatible
- Subject dashboard is at `/` → `/subject/maths` → `/quest/chapter/{N}` → questions
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- Never store or transmit any book page images/text to OpenAI
- Schema changes are handled by idempotent migrations in `session.py`
- OPENAI_API_KEY must be set in .env for tutor features to work
