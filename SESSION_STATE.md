# SESSION_STATE

## Current objective
EPIC 1 complete. Feed spec + YAML data files added. Ready to start EPIC 2.

## Completed this session
- EPIC 1 fully implemented (config, auth, UI, tests, ADRs)
- Added QUESTION_FEED_SPEC.md (template format contract)
- Added skills.yaml (15 skills across Ch5-8)
- Added templates_ch5_to_ch8.yaml (14 question templates)
- Updated TECH_SPEC with template engine section referencing feed spec
- Updated BACKLOG with expanded EPIC 2 items and test requirements
- Fixed .env.example to not contain real API key (moved to .env)

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic generation, seeded RNG
- Marking modes: exact_numeric, numeric_tolerance, rounding_dp, fraction_or_decimal, remainder_form, algebra_normal_form, order_match, mcq, exact_text_normalised
- OpenAI: only for polishing/hints/explanations, never for correctness

## Open questions
- Reward rules: XP-to-gold exchange rate + weekly cap (EPIC 4)
- Chart generation approach: matplotlib vs custom SVG (EPIC 3)
- Generator architecture: single dispatcher or per-type generator classes?

## Next actions (EPIC 2)
- [ ] Build YAML loader + Pydantic validation models for skills + templates
- [ ] Validate feed on startup (unique ids, skill exists, chapter match, supported types/marking modes)
- [ ] Implement deterministic parameter generators (seeded RNG per template type)
- [ ] Build marking engine with all supported modes
- [ ] Create QuestionInstance model (payload_json + correct_json) + persist
- [ ] Implement attempt logging + scoring
- [ ] Adaptive difficulty band tracking per user per skill
- [ ] Tests: loader validation, generator determinism, all marking modes

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- Never store or transmit any book page images/text to OpenAI
- IMPORTANT: Rotate the OpenAI API key -- it was briefly in .env.example (now fixed)
- Keep backups on second drive and outside git
