# SESSION_STATE

## Current objective
EPIC 2 complete. Template Question Engine fully implemented and tested.

## Completed this session
- EPIC 2 fully implemented:
  - YAML feed loader with Pydantic validation (feed_loader.py)
  - Feed validation on startup (fail-fast in lifespan)
  - 18 deterministic parameter generators (generators.py)
  - 9 marking modes (marking.py): exact_numeric, exact_text_normalised,
    numeric_tolerance, rounding_dp, fraction_or_decimal, remainder_form,
    algebra_normal_form, order_match, mcq
  - DB models: QuestionInstance, Attempt, UserSkillProgress (question.py)
  - Question generation service with answer-key computation (questions.py)
  - Quest API routes: chapter picker, question generation, answer submission (quest.py)
  - 3 HTML templates: quest_chapter, quest_question, quest_result
  - Adaptive difficulty: levels up after 3 correct, down on wrong
  - XP/Gold reward system scaled by difficulty band
  - Home page chapter cards now link to quest flow
  - ADR 005: Template Question Engine Architecture
- 78 tests passing (14 auth + 2 config + 14 loader + 47 generators/marking + 1 health)

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic, seed-based (ADR 005)
- Marking: 9 modes covering numeric, text, fraction, algebra, ordering, MCQ
- Generator registry: decorator-based dispatch by gen name
- Reward table: XP 5-40 by difficulty, Gold 1-8 for first-try correct
- Adaptive bands: 3 consecutive correct = level up, wrong = level down

## Open questions
- Reward rules: XP-to-gold exchange rate + weekly cap (EPIC 4)
- Chart/asset rendering: matplotlib SVG generation for pie/line charts (EPIC 3)
- OpenAI integration: hint ladder + mistake explanations (EPIC 5)

## Next actions (EPIC 3)
- [ ] Asset rendering: generate SVG/PNG for tables, pie charts, line graphs
- [ ] Wire asset rendering into quest question display
- [ ] Add chart templates to question HTML
- [ ] Tests for asset generation

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- SQLModel relationships require `List["Type"]` from typing (not `list["Type"]`)
- Never store or transmit any book page images/text to OpenAI
- IMPORTANT: Rotate the OpenAI API key -- it was briefly in .env.example (now fixed)
- Keep backups on second drive and outside git
