# SESSION_STATE

## Current objective
Minsterworth OS map study questions — complete. 18 real-map questions added, deployed, and tested.

## Completed this session

### Minsterworth OS Map Study (18 questions)
- **Static image serving**: Mounted `/images/` as StaticFiles in `main.py`; `map_image` asset renderer produces responsive `<img>` tags
- **`fixed` generator**: New generator that returns values as-is (no randomisation) for fixed/map-study questions
- **`keyword_any` marking mode**: Accepts answers matching any of a list of accepted keywords (case-insensitive substring)
- **`gridref_6fig` tolerance**: Updated marker to support `tolerance` (±N on 3rd/6th digits) and multiple accepted references
- **18 YAML templates**: Compass direction (3 MCQ), symbols (2 MCQ), features (1 MCQ), identification (2 short text), transport (1 MCQ), gridref 4-fig (2), gridref 6-fig (2 with tolerance), bearings (2 with ±5°), relief/contours (2 MCQ), settlement (1 MCQ)
- **10 new skills**: `geog.maps.*_realmap` skills for compass, symbols, features, identification, transport, gridref 4-fig, gridref 6-fig, bearing, relief, settlement
- **`_compute_answer` wiring**: Handles fixed-value templates (via `correct_value` param) for text, gridref, bearing, and keyword_any modes
- **Tests**: 48 new tests in `test_minsterworth.py` — fixed generator, map_image asset, keyword_any marker, gridref tolerance, bearing tolerance, template loading/validation
- **Docs**: ADR 019, quality test updated to allow `minsterworth_*` prefix
- 336 tests passing (288 existing + 48 new)
- Committed `6fc94e6`

## Completed this session

### EPIC 10: Per-Subject Progress Tracking
- **SubjectProgress model**: New `subject_progress` table with `user_id`, `subject`, `xp_earned`, `gold_earned`, `quests_completed`, `questions_answered`, `questions_correct`, `best_streak`, `last_played`
- **check_answer integration**: `_update_subject_progress()` called after every answer; derives subject from template → quest → fallback "maths"
- **Query helpers**: `get_subject_progress(db, user_id, subject)` and `get_all_subject_progress(db, user_id)` for single/multi lookup
- **Home page** (`home.html`): Subject cards show per-subject XP and quests completed badges
- **Subject home** (`subject_home.html`): Stats bar shows subject-specific XP, quests, correct/answered ratio, best streak (replaces global stats)
- **Admin dashboard** (`admin.html`): New per-subject breakdown card with XP, gold, quests, accuracy, questions done, best streak per subject
- **Pages routes**: `home_page` passes `subject_stats` dict; `subject_home` passes `sp` (SubjectProgress); `admin_page` passes `subject_stats` for kid user
- **Tests**: 15 new tests in `test_subject_progress.py` — model creation, `_update_subject_progress` upsert/increment, query helpers, integration with `check_answer`
- **Docs**: ADR 018, SESSION_STATE.md updated
- 288 tests passing (273 existing + 15 new)

### Bug fixes (this session)
- **Geography 500 error**: Live SQLite DB had NOT NULL on `question_instance.chapter`; added idempotent migration in `session.py` that recreates the table with nullable chapter column
- **Back link on question page**: Was hardcoded to `/` (home); now uses `_quest_back_link()` helper to navigate to parent unit/chapter/subject page; also refactored quest_summary to reuse same helper

### Unit Quest Standardisation
- **QuestSession model**: Added `subject` and `unit` optional fields; `chapter` now defaults to 0
- **QuestionInstance model**: `chapter` changed from required `int` to `Optional[int]` for non-maths subjects
- **DB migration**: Idempotent `ALTER TABLE ADD COLUMN` for `quest_session.subject` and `quest_session.unit`
- **generate_question / _select_template**: Accept `subject`/`unit` params; priority: `template_id > skill > unit > chapter`; unit selection uses `get_templates_by_unit()`
- **Quest routes**: `quest_start` accepts `subject`/`unit` form params; `quest_next` passes them through; `quest_summary` has dynamic back-link (unit page / chapter page / home)
- **quest_unit.html**: Added "Unit Quest" button (10 Qs, gold gradient, ⚔️ icon) matching the Chapter Quest pattern; skill forms also pass `subject`/`unit` hidden fields
- **quest_summary.html**: Dynamic back-link and play-again form include `subject`/`unit`/`chapter` as applicable
- **Tests**: 9 new tests in `test_unit_quest.py` — model fields, template selection, E2E generation, multi-skill coverage
- **Docs**: ADR 017, SESSION_STATE.md updated
- 273 tests passing (264 existing + 9 new)

### EPIC 9: Geography Content Pack (earlier this session)
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
- Per-subject progress tracking: denormalised SubjectProgress table, real-time increments, subject-specific UI (ADR 018)
- Real OS map study: fixed generator, map_image asset, gridref tolerance, 18 Minsterworth templates (ADR 019)

## Open questions
- None

## Next actions
- [ ] **BUG: Contour cross-section answers don't match the generated SVG profile** — generator/renderer mismatch, MCQ answers are hallucinated/wrong
- [ ] EPIC 10 continued: Normalised rewards balancing (per-subject XP rates, streaks/goals, parent caps)
- [ ] EPIC 11: History subject pack (YAML templates + generators)
- [ ] EPIC 12: Cross-subject features (combined leaderboard, subject streaks)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth

## Notes / gotchas
- Map images stored in `backend/app/images/`, served at `/images/` via StaticFiles mount
- `fixed` generator + `map_image` asset pattern is reusable for any place-study map
- Minsterworth template IDs use `minsterworth_*` prefix (quality test allows both `geog_*` and `minsterworth_*`)
- `gridref_6fig` tolerance: spec.tolerance ±N on 3rd/6th digits; spec.correct can list multiple accepted refs
- `keyword_any` marking: case-insensitive substring match against list of accepted answers
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
