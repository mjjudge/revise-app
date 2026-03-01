# SESSION_STATE

## Current objective
EPIC 4 complete. Gamification & Rewards system fully implemented and tested.

## Completed this session
- Fixed EPIC 2 backlog items (were not marked complete)
- EPIC 4 fully implemented:
  - QuestSession model: quest loops with progress, streak, and question tracking
  - Two quest modes: skill quest (8 Qs) and chapter quest (10 Qs)
  - Quest flow: POST /quest/start → question → answer → result → next → summary
  - Streak bonuses: +50% XP at 3 correct in a row, +100% at 5+
  - Weekly gold cap: default 100 gold/week, admin-configurable
  - Payout model: gold → cash conversion at 2p/gold, admin records payouts
  - Admin API: stats endpoint, payout recording, settings update
  - Admin dashboard: live stats, payout form, weekly cap control
  - Quest summary screen with accuracy %, rank system, best streak
  - Config additions: gold_to_pence (2), weekly_gold_cap (100)
  - 16 new gamification tests (106 total passing)
  - ADR 007: Gamification & Rewards System

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic, seed-based (ADR 005)
- Asset rendering: Pure inline SVG + HTML, no matplotlib (ADR 006)
- Gamification: Quest loops, streak bonuses, gold cap, payouts (ADR 007)
- Quest lengths: 8 for skill, 10 for chapter
- Streak bonus: +50% XP at 3 correct, +100% at 5+
- Gold conversion: 1 Gold = 2p
- Weekly gold cap: admin-configurable, default 100

## Open questions
- OpenAI integration: hint ladder + mistake explanations (EPIC 5)
- Hint penalties: should hints reduce gold reward? (EPIC 5)

## Next actions (EPIC 5)
- [ ] Tutor API endpoint (payload + attempt + user question)
- [ ] Prompt rules: age-appropriate, no personal data, don't jump to answer
- [ ] Hint ladder generation (optional)
- [ ] Logging + safety filters

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- SQLModel relationships require `List["Type"]` from typing (not `list["Type"]`)
- Never store or transmit any book page images/text to OpenAI
- IMPORTANT: Rotate the OpenAI API key -- it was briefly in .env.example (now fixed)
- Keep backups on second drive and outside git
- Schema changes require deleting data/app.sqlite3 before restart
- Weekly gold cap is in-memory only — resets on container restart
