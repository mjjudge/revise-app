# SESSION_STATE

## Current objective
EPIC 9 — Geography Content Pack: complete.

## Completed this session

### EPIC 9: Geography Content Pack
- **templates_geography.yaml**: 24 geography templates across 7 categories (knowledge MCQ, matching/grid-fill, scale calculations, map/grid ref, contours, climate graphs, weather diagrams)
- **generators.py**: ~15 new geography generators added — `pick_one`, `pick_one_distinct`, `from_object`, `geog_knowledge_mcq` (with knowledge pools for 4 topics), 6 matching-set generators (instruments, air masses, clouds, symbols, water cycle, continents/oceans), `map_scale`, `grid_map_with_features` (computes 4-fig and 6-fig grid refs), `compass_direction_mcq`, `climograph_dataset` (5 climate profiles), `climate_compare_mcq`, `synthetic_contour_map`, `isobar_chart_data`, `rainfall_diagram_data`
- **assets.py**: 9 new SVG renderers — `matching_cards`, `map_grid`, `compass_rose`, `scale_bar`, `climograph`, `contours`, `cross_section_set`, `synoptic_chart`, `rainfall_diagram`
- **marking.py**: 5 new marking modes — `gridref_4fig`, `gridref_6fig`, `bearing_3digit` (±tolerance), `grid_match` (JSON mapping with partial credit), `label_match` (alias)
- **questions.py**: Extended `_compute_answer` for geography modes + scale/contour/climograph numeric computation; added `_compute_grid_match`, `_compute_gridref`, `_compute_bearing`; added `get_grid_fill_data()` for matching UI
- **quest_question.html**: New `grid_fill` UI with dropdown `<select>` elements for matching left→right items, JSON answer, reset button
- **quest.py**: New `/quest/unit/{subject}/{unit}` route; `get_grid_fill_data` wired into all question-rendering routes
- **quest_unit.html**: New template for unit-based skill selection with breadcrumb navigation
- **pages.py**: Added geography to `_SUBJECT_META` with 4 units (maps, weather, climate, world)
- **home.html**: Geography card now active (no longer "Coming Soon")
- **quest_question.html**: Fixed chapter display for non-maths questions (conditional `Ch` label)
- **tests**: 56 new geography tests in `test_geography.py` — generator determinism, marking modes, E2E template generation, structure validation
- **Docs**: ADR 016, SESSION_STATE.md updated
- 264 tests passing (208 existing + 56 new)

### Bug fixes (earlier this session)
- Quests Done counter: fixed hardcoded `0` on home page
- Docker rebuild: `make restart` now includes `docker compose build`
- Stats on subject page: added quests_done query + stats bar

## Previous session work
- EPIC 8 — Multi-subject navigation framework (committed `85dc65b`)
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
- Geography content pack: 24 templates, 15 generators, 9 renderers, 5 marking modes (ADR 016)

## Open questions
- None

## Next actions
- [ ] EPIC 8.2: Subject-scoped progress tracking (per-subject XP/stats)
- [ ] EPIC 10: History subject pack (YAML templates + generators)
- [ ] EPIC 11: Cross-subject features (combined leaderboard, subject streaks)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth

## Notes / gotchas
- Geography uses unit-based routing (`/quest/unit/geography/{unit}`) not chapter-based
- Grid-fill UI uses `<select>` dropdowns → JSON answer in hidden field → `grid_match` marker
- All matching-set generators return `{left, right, correct_mapping}` structure
- `grid_map_with_features` computes both 4-fig and 6-fig grid refs per feature point
- Climograph dataset supports 5 climate profiles (temperate, tropical, mediterranean, polar, tropical_dry)
- Contour map generator supports 3 styles (hill, landform, cross_section)
- Bearing marker supports wrapping around 360°/0°
- feed_loader cache must be cleared between tests (autouse fixture handles this)
- E2E quality tests cover both maths and geography templates
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- Never store or transmit any book page images/text to OpenAI
- Schema changes are handled by idempotent migrations in session.py
- OPENAI_API_KEY must be set in .env for tutor features to work
