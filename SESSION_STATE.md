# SESSION_STATE

## Current objective
EPIC 6.7 complete. Adventurer tier system with Greek mythology themes.

## Completed this session
- EPIC 4 fully implemented (gamification, quest sessions, payouts)
- EPIC 5 fully implemented (OpenAI tutor — Professor Quill)
- Fixed leaked API key in git history (git-filter-repo + force-push)
- EPIC 6 fully implemented:
  - Structured logging: `core/logging.py` with JSON (prod) and coloured (dev) formatters
  - Request logging middleware: method, path, status, duration_ms with request_id
  - Themed error pages: 404/500/403 with fantasy messaging + `error.html`
  - HTMX error toast: `responseError` listener for failed AJAX requests
  - Retry UX: HTML5 `required` + server-side empty-answer inline error with red border
  - YAML cross-validation tests (7): skills exist, chapters match, marking modes supported, solution steps, ID prefixes, difficulty distribution, chapter coverage
  - End-to-end generation tests (5): every template generates, marks correct, marks wrong, deterministic with same seed, different seeds produce variety
  - Logging tests (7): JSON/Dev formatter output, extras, level override, no duplicates
  - Error page tests (4): 404 themed, home link, health unaffected, empty answer inline
  - Bug fixes found by E2E tests:
    - `mark_rounding_dp`: was reading raw `dp_from_param` string instead of resolved `dp` value
    - `mark_fraction_or_decimal`: `rounding` could be `None`, causing AttributeError
  - 23 new tests in `test_quality.py` (151 total passing)
  - ADR 009: Quality & Observability
- Doubled question bank:
  - 15 new v2 templates added (30 total across Ch5-8)
  - Each skill now has 2 templates at different difficulty levels
  - All 30 templates pass E2E generation, correct-marking, and wrong-marking tests
  - Fixed `_compute_algebra` to include variable name in answer dict
- EPIC 6.5 fully implemented:
  - `calculator` field on `TemplateDef` (optional: "basic" or "scientific") with Pydantic validator
  - 16 templates tagged with `calculator: basic` (mean, pie chart, substitution, metric, rounding, BIDMAS, division, experimental probability — both v1 and v2)
  - On-screen calculator panel: toggle button (🧮), 4×5 grid (digits, operators, clear, backspace, equals), read-only display, "Copy to answer" button
  - Calculator wired through `quest.py` — all 3 `quest_question.html` render calls pass `calculator` from template
  - 2 new calculator tests in `test_quality.py` (field values + tagged template count)
  - ADR 010: On-screen Calculator
- Weekly gold cap increased from 100 to 500 (£10/week at 2p/gold)
- EPIC 6.6 fully implemented:
  - `detect_milestone(old_xp, new_xp)` helper in `questions.py` — detects 100-XP boundary crossings
  - `milestone_message(xp)` — 6 rotating title/body pairs with fantasy theme
  - Canvas fireworks animation: 8 staggered bursts, coloured particles with gravity decay
  - Mini 4×4 Sudoku reward game: 6 pre-built puzzles, input validation (1-4 only), check/close
  - Milestone banner on `quest_result.html` with "🧩 Play a Reward Game!" button
  - Wired into `quest_answer()` — captures `old_xp` before `check_answer()`, detects milestone, passes to template
  - 15 new milestone tests (detect_milestone, milestone_message, integration)
  - ADR 011: Milestone Celebrations
- EPIC 6.7 fully implemented:
  - `services/tiers.py`: 9-tier Greek mythology progression system (Mortal → Heir of Olympus)
  - Each tier has unique colour scheme (accent, glow, gradient, badge)
  - `base.html`: body gradient + CSS custom properties change per tier
  - `templates/shared.py`: Jinja2 template factory with tier globals
  - Tier badge in all page navbars (icon + title pill)
  - Home page: tier progress card with progress bar, XP tracker, and full tier roadmap
  - `detect_tier_up()` in `quest_answer` — banner celebration on tier crossings
  - 28 new tests in `test_tiers.py` (get_tier, tier_progress, detect_tier_up, data integrity)
  - ADR 012: Adventurer Tier System

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

## Open questions
- None for current EPICs

## Next actions (EPIC 7 — Hardening)
- [x] Increase weekly gold cap to 500 (£10/week)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth
- [ ] Consider adding more v3 templates for skills with low coverage
- [ ] Consider adding more mini-games (word search, memory match) for milestone variety
- [ ] Consider persisting highest tier reached for permanent badges

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
- OPENAI_API_KEY must be set in .env for tutor features to work
- Tutor features degrade gracefully if API key is missing or API is down
