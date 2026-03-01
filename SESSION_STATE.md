# SESSION_STATE

## Current objective
EPIC 3 complete. Charts/Tables asset rendering fully implemented and tested.

## Completed this session
- EPIC 3 fully implemented:
  - Pure SVG asset rendering engine (assets.py) — no external dependencies
  - Four asset types: table (HTML+Tailwind), line chart (SVG), pie chart (SVG), spinner (SVG)
  - Conditional rendering via `when` expressions on asset specs
  - Dotted reference resolution for nested params (e.g. `dataset.x`)
  - Static row `{param}` substitution with arithmetic expression support
  - Pre-rendered HTML stored in `QuestionInstance.assets_html` column
  - Wired into question generation service (questions.py)
  - Display in quest_question.html via `{{ question.assets_html | safe }}`
  - 12 asset tests (tables, line charts, pie charts, spinners, conditionals)
  - ADR 006: Charts/Tables Asset Rendering
- 90 tests passing (12 assets + 14 auth + 2 config + 14 loader + 47 generators/marking + 1 health)

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic, seed-based (ADR 005)
- Asset rendering: Pure inline SVG + HTML, no matplotlib (ADR 006)
- Marking: 9 modes covering numeric, text, fraction, algebra, ordering, MCQ
- Generator registry: decorator-based dispatch by gen name
- Reward table: XP 5-40 by difficulty, Gold 1-8 for first-try correct
- Adaptive bands: 3 consecutive correct = level up, wrong = level down

## Open questions
- Reward rules: XP-to-gold exchange rate + weekly cap (EPIC 4)
- OpenAI integration: hint ladder + mistake explanations (EPIC 5)

## Next actions (EPIC 4)
- [ ] Points model + streak rules + hint penalties
- [ ] Wallet + payout ledger (admin)
- [ ] Quest flow (8-12 Q loop) + summary screen
- [ ] Weekly cap + admin controls

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- SQLModel relationships require `List["Type"]` from typing (not `list["Type"]`)
- Never store or transmit any book page images/text to OpenAI
- IMPORTANT: Rotate the OpenAI API key -- it was briefly in .env.example (now fixed)
- Keep backups on second drive and outside git
- Schema changes require deleting data/app.sqlite3 before restart
