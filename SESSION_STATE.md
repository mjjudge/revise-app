# SESSION_STATE

## Current objective
EPIC 10.7 — "Teach Me" Mini-Lessons implemented and deployed.

## Completed this session

### EPIC 10.7 — "Teach Me" AI Mini-Lessons
- **Feature**: "Teach Me" button on question page + result page (wrong answers) opens modal with AI-generated KS3-style lesson
- **Subject-aware**: Maths and geography get different lesson structures (maths: worked example, steps; geography: key facts, real-world example)
- **Tutor service**: New `generate_lesson()` function with dedicated system prompts (`_LESSON_SYSTEM_MATHS`, `_LESSON_SYSTEM_GEOGRAPHY`)
- **API endpoint**: `POST /tutor/lesson` returns styled HTML fragment, cached on `QuestionInstance.lesson_html`
- **Markdown-to-HTML converter**: `_lesson_to_html()` converts GPT markdown output to styled HTML (headings, lists, bold/italic)
- **Modal popup**: Full-screen overlay with loading spinner, escape/backdrop close, "Try the Question" button
- **No gold penalty**: Lessons are free — encouraging learning without cost
- **Schema**: New `lesson_html` field on `QuestionInstance` for caching
- **Tests**: 13 new tests (431 total passing)
- **ADR**: 023-teach-me-mini-lessons.md

### Parallelogram Fix
- Fixed tangram parallelogram polygon from `[[0,0],[60,0],[85,50],[25,50]]` to `[[0,0],[50,0],[100,50],[50,50]]`
- Updated DEFAULT_PIECES, 5 seed files, 6 runtime data files

### EPIC 10.6 — Brain Reset Reward Mini-Games
- **Game framework**: Created `backend/app/static/reward_games.js` with registry pattern, modal system, random game selection, skip button
- **10 games implemented** (all pure client-side JS):
  1. Mini Sudoku (fixed) — 4×4 grid with inline styles (fixes broken Jinja2 block issue)
  2. Tic-Tac-Toe — vs simple AI (win/block/prefer-centre strategy)
  3. Space Invaders — canvas, 45s arcade, mobile touch controls
  4. Pattern Memory — 4×4 grid sequence recall with difficulty scaling
  5. Reflex Tap — 10 rounds, average reaction time
  6. Word Scramble — 60s, unscramble maths/geography vocabulary
  7. Mini 2048 — tile-merging, target 256, swipe support
  8. Gravity Collector — canvas physics, 45s, orbiting star collection
  9. Tangram Builder — tap cells to fill shape silhouettes
  10. Pixel Art Reveal — tap tiles to reveal castle/cat/landscape art
- **Admin Games page**: `/admin/games` with preview buttons and on/off toggles per game
- **Game config service**: `backend/app/services/game_config.py` — JSON file persistence, toggle API
- **Static file serving**: Added `/static` mount in main.py
- **Milestone integration**: Random enabled game on every 100 XP milestone
- **Sudoku fix**: Moved from Jinja2 conditional blocks to inline styles in JS — root cause was `{% block head %}` wrapped in `{% if milestone %}` which doesn't work reliably in Jinja2 inheritance
- **Tests**: 12 new tests in `test_reward_games.py`
- **Docs**: ADR-022, BACKLOG EPIC 10.6
- 402 tests passing (390 existing + 12 new)

### EPIC 10.5 — Practice Boost: Extra Rewards for Weak Skills
- **`get_boosted_skills(db, user_id)`**: New service function returns skill codes qualifying for Practice Boost (accuracy ≤60% with ≥3 attempts, or band==1). Auto-removes when accuracy ≥75% over ≥5 attempts.
- **`check_answer()` boost multiplier**: Now returns `(attempt, result, is_boosted)` 3-tuple. When skill is boosted: 2× gold, 1.5× XP. Applied after streak bonus, before hint penalty and weekly cap.
- **quest_unit.html**: Boosted skills show ⚡💎 badge with gold border and "2× Gold" label
- **quest_question.html**: "Practice Boost Active — 2× Gold & 1.5× XP!" banner when answering boosted skill
- **quest_result.html**: "Practice Boost! 2× Gold & 1.5× XP" callout on correct answers for boosted skills
- **admin.html**: "⚡ Boosted" badge next to weak skills in Skill Insights card
- **Tests**: 15 new tests in `test_practice_boost.py` — `get_boosted_skills` (10 tests: empty, threshold exclusion, low accuracy, band 1, auto-remove, boundary cases) + reward multiplier (5 tests: double gold, 1.5× XP, non-boosted normal, streak+boost stacking, weekly cap still applies, wrong answer)
- **All callers updated**: `check_answer()` return changed from 2-tuple to 3-tuple; updated quest.py, test_gamification.py, test_tutor.py, test_quality.py, test_subject_progress.py
- **Docs**: ADR 021
- 390 tests passing (375 existing + 15 new)

### Question repeat prevention (ADR 020)
- `_exclude_recent()` helper filters recently-used templates; falls back to full list
- `_select_template()` and `generate_question()` accept `exclude_template_ids`
- `quest_next` builds exclude set from quest's question IDs via `_recent_template_ids()`
- 7 tests in `test_repeat_prevention.py`

### Rollback tooling
- `scripts/rollback_today.sh` — date-based rollback for XP/gold/attempts/quests
- Makefile targets: `make rollback-today` and `make rollback-date DATE=YYYY-MM-DD`
- Fixed subject_progress rollback to use quest_session join (skill prefix mismatch)

### Admin Skill Insights
- `get_skill_insights(db, user_id, top_n=3)` — strongest/weakest per subject by accuracy
- Admin dashboard card with green/red accuracy bars per subject
- Maths subject_progress backfilled from attempt history (777 XP, 99 gold, 48 Qs)
- 6 tests in `test_subject_progress.py`

### Skill merging (Maps unit)
- Merged 6 `*_realmap` skills into base counterparts (20→14 skills)

### Bug fixes
- `gridref_6fig` tolerance crash: `spec.get("tolerance", 0)` returns None → fixed to `or` pattern
- Railway question reworded

### North Evesham map questions
- 20 questions with answers added

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
- Question repeat prevention: template exclusion within quests (ADR 020)
- Practice Boost: 2× gold + 1.5× XP for weak skills, auto-remove at 75% (ADR 021)

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
