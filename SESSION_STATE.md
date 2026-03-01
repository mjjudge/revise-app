# SESSION_STATE

## Current objective
EPIC 1 (MVP App Shell) is COMPLETE. Ready for EPIC 2,

## Completed this session
- EPIC 1 fully implemented:
  - Pydantic Settings config module (env vars, child name/nicknames)
  - SQLModel User model with bcrypt PIN hashing
  - DB init + seed on startup (Anna kid + Parent admin)
  - Signed session cookies (itsdangerous) for auth
  - Auth routes: POST /auth/login, GET /auth/logout
  - Jinja2 + HTMX + Tailwind base template with fantasy theme
  - Login page with user selection cards + 4-digit PIN pad (iPad-friendly)
  - Home page with quest chapter cards, XP/Gold display, adventure greeting
  - Admin dashboard with progress view + reward control placeholders
  - 14 passing backend tests (config, auth flow, health)
  - 4 ADRs: UI stack, auth model, theme, adaptive difficulty
  - Updated TECH_SPEC with all design decisions

## Decisions made (this session)
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- User model: Anna (kid) + Parent (admin), simple two-user system
- Hatch build system for proper package install via uv
- StaticPool for in-memory SQLite test isolation

## Open questions
- Reward rules: XP-to-gold exchange rate + weekly cap (EPIC 4)
- Template engine API design (EPIC 2)
- Chart generation approach: matplotlib vs custom SVG (EPIC 3)

## Next actions
- [ ] EPIC 2: Define skill taxonomy for Ch5-8
- [ ] EPIC 2: Build template interface + registry
- [ ] EPIC 2: Implement first batch of question templates
- [ ] EPIC 2: Marking rules + attempt logging
- [ ] EPIC 2: Adaptive difficulty band tracking per user per skill

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses `uv sync` without --frozen)
- Tests require `--extra dev` flag: `uv run --extra dev pytest`
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- Never store or transmit any book page images/text to OpenAI
- Keep backups on second drive and outside git
