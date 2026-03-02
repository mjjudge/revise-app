# BACKLOG

## EPIC 0 -- Repo + Build Foundation
- [x] Scaffold repo structure (backend, frontend, docs, ops)
- [x] Docker Compose + Caddy proxy
- [x] Makefile commands: build/up/down/restart/logs/test/backup
- [x] Git hygiene: .gitignore includes backups/data/logs
- [x] Docs: TECH_SPEC, decisions folder, session tracking
- [x] Add QUESTION_FEED spec and initial YAML feeds (skills + templates)
- [x] Add YAML validation test to ensure templates reference valid skills and supported marking modes

## EPIC 1 -- MVP App Shell
- [x] App config + env loading (Pydantic Settings)
- [x] Simple PIN auth (kid/admin) with signed session cookies
- [x] User model (SQLModel) + bcrypt PIN hashing + seed on startup
- [x] Jinja2 + HTMX + Tailwind base template (fantasy theme)
- [x] Login page (user selection + 4-digit PIN pad)
- [x] Home page (quest launcher, XP/Gold display, chapter cards)
- [x] Admin dashboard (progress view + reward controls placeholder)
- [x] Backend tests: 14 tests (config, auth flow, health)
- [x] ADRs: 001 UI stack, 002 auth model, 003 theme, 004 adaptive difficulty
- [x] Persistent SQLite setup

## EPIC 2 -- Template Question Engine (Ch5-8 core)
- [x] Skill taxonomy + difficulty bands
- [x] Template interface + registry
- [x] Implement template loader for YAML feeds (skills.yaml + templates_ch5_to_ch8.yaml)
- [x] Validate feed on startup (unique ids, skill exists, chapter match, supported types/marking modes)
- [x] Deterministic generator framework (seeded) to expand template parameters into an instance payload
- [x] Persist generated instance payload_json + correct_json for replay/review
- [x] Implement 8-12 templates spanning chapters 5-8
- [x] Doubled question bank: 15 v2 templates (30 total) with varied difficulty and wording
- [x] Deterministic answer keys + marking rules
- [x] Question persistence + attempt logging
- [x] Adaptive difficulty band adjustment
### EPIC 2 -- Tests
- [x] Tests: template loading + schema validation
- [x] Tests: generator determinism (same seed => same instance)
- [x] Tests: marking modes (numeric tolerance, rounding, fraction/decimal equivalence, remainder form, ordering)

## EPIC 3 -- Charts/Tables Assets
- [x] SVG pie chart generator
- [x] Line graph generator (pure SVG)
- [x] Table rendering component (HTML + Tailwind)
- [x] Spinner renderer (SVG)
- [x] Conditional asset rendering (when expressions)
- [x] Assets wired into question generation + stored in DB
- [x] 12 asset rendering tests
- [x] ADR 006: Charts/Tables Asset Rendering

## EPIC 4 -- Gamification + Rewards
- [x] QuestSession model (8Q skill / 10Q chapter loops)
- [x] Quest flow: start → question → answer → result → next → summary
- [x] Streak bonus: +50% XP at 3 correct, +100% at 5 correct (within quest)
- [x] Weekly gold cap (admin-configurable, default 100)
- [x] Payout model + admin payout API (gold → cash at 2p/gold)
- [x] Admin dashboard: live stats, payout form, reward controls
- [x] Quest summary screen with rank (Legendary/Epic/Brave/Apprentice)
- [x] Config: gold_to_pence, weekly_gold_cap
- [x] 16 gamification tests (106 total)
- [x] ADR 007: Gamification & Rewards System

## EPIC 5 -- Tutor Mode (OpenAI)
- [x] Tutor API endpoint (payload + attempt + user question)
- [x] Prompt rules: age-appropriate, no personal data, don't jump to answer
- [x] Hint ladder generation (3-level: nudge → worked step → nearly-the-answer)
- [x] Fun rewrite of question stems (cached)
- [x] Hint penalty (halves gold reward)
- [x] Logging + safety filters
- [x] 22 tutor tests (128 total)
- [x] ADR 008: Tutor Mode — OpenAI Integration

## EPIC 6 -- Quality + Observability
- [x] Structured logging (JSON prod / coloured dev) with `core/logging.py`
- [x] Request logging middleware (method, path, status, duration_ms)
- [x] Themed error pages (404/500/403) with `error.html`
- [x] HTMX error toast for failed AJAX requests
- [x] Retry UX: HTML5 `required` + server-side empty-answer inline error
- [x] YAML validation tests (skills, chapters, marking modes, solution steps, ID prefixes, difficulty)
- [x] End-to-end template generation tests (generate, mark correct, mark wrong, determinism, seed variety)
- [x] Logging + error page tests
- [x] Bug fixes: `mark_rounding_dp` dp_from_param, `mark_fraction_or_decimal` rounding None
- [x] 23 quality tests (151 total)
- [x] ADR 009: Quality & Observability

## EPIC 6.5 -- On-screen Calculator
- [x] Add `calculator` field to `TemplateDef` schema (optional: "basic" or "scientific")
- [x] Tag 16 templates with `calculator: basic` (mean, pie chart, substitution, metric, rounding, BIDMAS, division, experimental probability — v1+v2)
- [x] Build toggle-able calculator panel (digit/operator grid, display, Copy to answer)
- [x] Wire `calculator` flag through `quest.py` to all 3 question render calls
- [x] Calculator field validation tests + tagged-template count test
- [x] 153 total tests passing
- [x] ADR 010: On-screen Calculator

## EPIC 6.6 -- Milestone Celebrations & Easter Eggs
- [x] `detect_milestone()` helper: detects when XP crosses a 100-point boundary
- [x] `milestone_message()`: 6 cycling congratulatory titles/messages
- [x] Canvas-based fireworks animation (8 bursts, coloured particles, gravity)
- [x] Mini 4×4 Sudoku reward game (6 pre-built puzzles, validation, themed UI)
- [x] Milestone banner + "Play a Reward Game!" button on result page
- [x] Wired into `quest_answer` flow (captures old_xp, detects crossing, passes to template)
- [x] 15 milestone tests (168 total passing)
- [x] ADR 011: Milestone Celebrations

## EPIC 6.7 -- Adventurer Tiers (Greek Mythology)
- [x] 9-tier system: Mortal → Acolyte of Athena → Messenger of Hermes → Warrior of Ares → Artisan of Hephaestus → Hunter of Artemis → Champion of Apollo → Favoured of Poseidon → Heir of Olympus
- [x] Dynamic theme colours per tier (body gradient + accent + glow via CSS custom properties)
- [x] Shared Jinja2 template factory with tier globals (`get_tier`, `tier_progress`, `all_tiers`)
- [x] Tier badge in navbar across all pages
- [x] Home page: tier progress card with bar, XP tracker, full roadmap
- [x] Tier-up celebration banner on result page
- [x] 28 tier tests (196 total passing)
- [x] ADR 012: Adventurer Tier System

## EPIC 7 -- Hardening (LAN-only, optional)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth
- [ ] Optional Tailscale access

## EPIC 8 — Multi-subject Navigation (Maths + Geography + History soon) ✅
Goal: Add subject-level organisation without forcing users to bounce back to the top after every action.
Anna should:
1) log in → see subjects (Maths, Geography, History coming soon) + progress per subject
2) enter a subject → see quests (units/chapters) + progress
3) drill into quest → see skills/subskills
4) answer questions continuously while staying in that subject context
Switching subjects is done via a top navigation link, not by forcing a return.

### Stories
- [x] Define subject hierarchy model:
      Subject → Unit/Quest → Skill → Template → Question Instance
- [x] Update feed spec to support subject/unit fields in skills + templates
- [x] Update backend selection API to accept subject/unit filters
- [x] Update frontend routing/state to retain current subject context
- [x] Add top navigation subject switcher (persistent header)

### Tasks (backend)
- [x] Update template loader to accept optional fields on skills/templates:
      `subject`, `unit` (and keep backward compatibility with maths/chapter fields)
- [x] Maths chapter-to-unit mapping:
      - Ch5 → unit `data` (Data & Charts)
      - Ch6 → unit `algebra` (Expressions & Formulae)
      - Ch7 → unit `calculation` (Calculation & Measure)
      - Ch8 → unit `probability` (Probability)
- [x] Add validation rules:
      - template.subject must match skill.subject (if both present)
      - template.unit must match skill.unit (if both present)
      - ids unique; marking modes supported
- [x] Extend DB schema (migration):
      - Add columns: questions.subject, questions.unit, questions.skill_code (if not already)
      - Add columns: attempts.subject/unit (or derive via join if you prefer)
- [x] Add/extend endpoints:
      - GET /subjects (list subjects + progress summary)
      - GET /subjects/{subject}/quests (list units/quests + progress)
      - GET /subjects/{subject}/quests/{unit}/skills (list skills + progress)
      - POST /subjects/{subject}/start (start quest within subject context)
- [x] Update scoring/progress rollups to group by subject/unit/skill

### 8.1 — Unit Quest Standardisation
- [x] QuestSession model: subject/unit fields, chapter default 0
- [x] QuestionInstance.chapter: Optional[int] for non-maths
- [x] DB migration for quest_session.subject/unit
- [x] generate_question / _select_template: subject/unit params
- [x] Quest routes: start/next/summary handle unit quests
- [x] quest_unit.html: Unit Quest button (10 Qs, gold gradient)
- [x] quest_summary.html: dynamic back-link per subject
- [x] 9 unit quest tests (273 total)
- [x] ADR 015, 017

### Tasks (frontend)
- [x] New landing page after login:
      - subject cards: Maths, Geography, History (coming soon)
      - show progress bars and current level per subject
- [x] Subject home page:
      - quest/unit list with progress and recommended next quest
- [x] Quest page:
      - skills/subskills list (or a curated skill set)
- [x] Persistent top bar:
      - current subject shown
      - “Switch subject” dropdown or links
      - does NOT auto-navigate away after each question
- [x] Ensure “Back” behaviour stays within subject:
      question → quest → subject home (not global home unless explicitly clicked)

### Tests
- [x] Backend tests:
      - template loader backwards compatibility (maths still loads)
      - subject/unit filtering selection
      - progress rollups by subject
- [x] Frontend tests:
      - smoke navigation: login → subject → quest → question → next question without losing context


## EPIC 9 — Geography Content Pack (YAML + Generators + Renderers) ✅
Goal: Add KS3 Geography practice using template-driven generation and generated graphics (maps, contours, climographs).

### Stories
- [x] Add Geography skills + templates YAML pack into repo
- [x] Implement required generators (seeded, deterministic)
- [x] Implement required renderers (SVG)
- [x] Implement marking modes for geo-specific answers
- [x] Add Geography quests/units and progress tracking

### Tasks (content)
- [x] Add `skills_geography.yaml` and `templates_geography.yaml`
- [x] Decide units/quests naming (e.g. "Maps", "Weather", "Climate", "World")
- [x] Map templates to quest buckets

### Tasks (generators)
- [x] Map/grid generator:
      - deterministic point placement, labelled axes, feature names
- [x] Compass/bearing helpers:
      - direction between points (8-point)
      - bearing calculation (degrees from north clockwise)
- [x] Grid reference helpers:
      - 4-figure grid refs (square)
      - 6-figure grid refs (tenths within square)
- [x] Scale helpers:
      - ratio-based and bar-scale-based conversions
- [x] Contour generators:
      - synthetic hill contours (interval, peak)
      - landform patterns (steep/gentle/valley/ridge)
      - cutline generator for A–B
      - cross-section option generator (correct + plausible distractors)
- [x] Climate generators:
      - climograph dataset generator (temperate/tropical/med/etc)
      - compare generator (identify which is tropical and why)
- [x] Weather generators:
      - isobar chart generator (H/L + tight/loose spacing)
      - rainfall diagram generator (relief/convectional/frontal)
      - water cycle diagram generator
      - cloud set generator (simple silhouettes)

### Tasks (renderers: SVG)
- [x] `map_grid` renderer (SVG)
- [x] `compass_rose` renderer (SVG)
- [x] `scale_bar` renderer (SVG)
- [x] `contours` renderer (SVG)
- [x] `cross_section_set` renderer (SVG for answer options)
- [x] `climograph` renderer (SVG)
- [x] `synoptic_chart` renderer (SVG)
- [x] `diagram_label` renderer (SVG)

### Tasks (marking)
- [x] New marking modes:
      - gridref_4fig normalisation + validation
      - gridref_6fig normalisation + validation
      - bearing_3digit with tolerance
      - label_match for diagram/map labels
- [x] Ensure marking returns structured feedback:
      - correct/incorrect
      - brief reason
      - common mistake hint (optional)

### Tasks (UI/UX)
- [x] New question components:
      - map display (SVG)
      - label-match / grid-fill UI
      - cross-section MCQ with visuals
      - climograph questions (read values)
- [x] Add Geography quest selection screens and progress bars
- [ ] Add "Stephen running from what?" story mode (Phase 2 — deferred):
      - map-driven narrative questions (generated scenes, not copied text)

### Tests
- [x] Determinism tests (same seed ⇒ identical SVG + answers)
- [x] Geometry sanity tests (bearing correctness, grid refs within bounds)
- [x] Renderer tests (snapshot-style or pixel hash for SVG output)
- [x] End-to-end smoke: start Geography quest → answer 5 Q → XP/gold updates


## EPIC 10 — Subject Progress, Levels and Rewards Balancing
Goal: Make XP/Gold feel fair across different subjects and question types.

- [ ] Define per-subject level curves (or shared curve)
- [ ] Normalise rewards by difficulty + time + hints used
- [ ] Add per-subject streaks and per-subject weekly goals (optional)
- [ ] Parent controls per subject (caps, multipliers)


## EPIC 10.5 — Practice Boost: Extra Rewards for Weak Skills
Goal: Encourage Anna to practise skills she struggles with by offering bonus gold
and XP when she attempts "needs practice" skills, rather than farming comfortable ones.

**Context**: The Skill Insights feature (admin dashboard) shows that Anna gravitates
to high-accuracy skills to build gold, while avoiding weaker skills. This EPIC adds
a "Practice Boost" multiplier to incentivise working on skills where accuracy is low.

### Design
A skill qualifies for **Practice Boost** when:
- ≥3 attempts exist (enough data to be meaningful)
- Accuracy is ≤60% (struggling threshold)
- OR the skill's difficulty band has dropped to 1 (adaptive system already flagged it)

Boost rewards:
- **2× gold** on correct first-try answers for boosted skills
- **1.5× XP** on any correct answer for boosted skills
- Visual indicator on the quest/skill UI so Anna knows which skills have a boost active
- Boost **removes itself** once accuracy on that skill reaches 75%+ (over ≥5 attempts)

The boost should feel like a positive incentive ("bonus treasure for brave adventurers!")
rather than a penalty for staying on easy skills.

### Stories
- [x] **10.5.1 — Identify boosted skills**: Add `get_boosted_skills(db, user_id)` service
      that returns skill codes qualifying for Practice Boost based on accuracy/band thresholds
- [x] **10.5.2 — Apply reward multiplier**: In `check_answer`, detect if the current
      question's skill is boosted and apply 2× gold / 1.5× XP multiplier
      (after streak bonus, before weekly cap)
- [x] **10.5.3 — Boost badge on skill UI**: Show a ⚡ or 💎 badge next to boosted skills
      on the unit quest page (quest_unit.html) so Anna sees which ones give bonus treasure
- [x] **10.5.4 — Boost notification on result**: When a boosted skill pays out, show
      "Practice Boost! 2× Gold 💎" on the result page so the reward feels tangible
- [x] **10.5.5 — Auto-remove boost**: When a skill's accuracy crosses 75% threshold
      (≥5 attempts), the boost is removed — the skill has been practised enough
- [x] **10.5.6 — Admin visibility**: Show boosted skills on the admin dashboard
      (Skill Insights card), marked with a boost indicator

### Tasks (backend)
- [x] Add `get_boosted_skills()` to `services/questions.py`:
      - Query `UserSkillProgress` for skills where accuracy ≤60% AND attempts ≥3,
        OR current_band == 1
      - Return set of skill codes
- [x] Update `check_answer()` reward calculation:
      - After base XP/gold but before weekly cap
      - If skill is in boosted set: `gold = gold * 2`, `xp = int(xp * 1.5)`
      - Store boost flag in attempt (or derive from skill state at time of answer)
- [x] Add boost status to quest/skill selection API responses
- [x] Update `get_skill_insights()` to flag boosted skills

### Tasks (frontend)
- [x] quest_unit.html: Add boost badge (⚡💎) next to skill names that qualify
- [x] quest_question.html: Optional "Practice Boost active!" banner at top
- [x] quest_result.html: "Practice Boost! 2× Gold 💎" callout on correct answers
- [x] Admin dashboard: Boost indicator in Skill Insights card

### Tests
- [x] `get_boosted_skills` returns correct skills based on accuracy threshold
- [x] `get_boosted_skills` excludes skills with <3 attempts
- [x] `check_answer` applies 2× gold for boosted skill (correct, first try)
- [x] `check_answer` applies 1.5× XP for boosted skill
- [x] Boost does not apply when accuracy >60%
- [x] Boost auto-removes when accuracy crosses 75%
- [x] Weekly gold cap still applies after boost multiplier
- [x] Streak bonus and boost stack correctly (streak first, then boost)


## EPIC 10.6 — Brain Reset Reward Games
Goal: Provide 10 lightweight, fun mini-games as "Brain Reset Rewards" triggered on
milestone celebrations. Games are max 90 seconds, no penalties, no leaderboard
pressure. Includes an admin Games page to preview and toggle games on/off.

**Design principles**:
- Max 90 seconds per game
- No penalties or deep scoring — they are rewards, not challenges
- Optional skip button on every game
- Pure client-side JS (no server round-trips during play)
- Games are offered at milestones (every 100 XP) — one random enabled game
- Admin can test any game and toggle which ones are in the rotation

### Games

1. **Mini Sudoku** (fix existing) — 4×4 grid, fill blanks so rows/cols/boxes have 1–4.
   Bug: grid renders empty with no given numbers and inputs not editable. Fix the
   existing `openSudoku()` JS + CSS in quest_result.html.

2. **Tic-Tac-Toe vs Computer** — Classic 3×3 grid, Anna plays X against a simple
   AI (random moves or one-step lookahead). Win/draw/lose with fun messages.

3. **Space Invaders Mini** — Canvas game. Arrow keys to move ship, spacebar to fire.
   3 rows of aliens descend slowly. No lives system — just "how many can you zap
   in 60 seconds?" with a score counter.

4. **Pattern Memory** — Show a 4×4 grid, highlight 5–8 squares in sequence (1/sec),
   hide them, Anna taps them back in order. Difficulty: more squares, faster reveal.
   "Mini Memory Mission" branding.

5. **Tangram Builder** — Show a silhouette (boat, house, cat, arrow, etc). Provide
   7 geometric shapes. Drag & rotate to fill the silhouette. Gentle snap-to-grid,
   no timer, no fail state — just encouragement.

6. **Reflex Tap** — Circle appears randomly on screen, tap as fast as possible.
   10 rounds, shows average reaction time. "Beat your best!" messaging.
   Random fake-outs (faint circle before solid).

7. **Word Scramble** — Scrambled subject vocabulary (TROPOSPHERE → PHERESORTOP,
   CONTOUR → RUCONTO). 30 seconds to unscramble 5 words. No penalty, bonus feel.
   Word bank drawn from geography/maths terms Anna has studied.

8. **Pixel Art Reveal** — Long-term: earning XP reveals tiles of a hidden pixel
   image (cat, castle, landscape). Each milestone unlocks a chunk. No time pressure.
   Progress persists across sessions.

9. **Gravity Collector** — Canvas game. Control a small planet with arrow keys,
   collect stars while orbiting a centre object. Simple physics, no enemies.
   60-second session, count stars collected.

10. **Mini 2048** — 4×4 number grid, arrow keys to slide, combine matching tiles.
    Short version: stop at 128 or 256. Shows "You reached [highest tile]!"

### Stories
- [ ] **10.6.1 — Fix Mini Sudoku**: Debug and fix existing 4×4 Sudoku so grid
      renders with given numbers, inputs accept digits, and check works correctly
- [ ] **10.6.2 — Game framework**: Create `reward_games.js` module with game
      registry, random selection, modal/overlay system, skip button, and completion
      callback. Each game is a self-contained function that renders into a container.
- [ ] **10.6.3 — Tic-Tac-Toe**: Implement 3×3 grid with simple AI opponent
- [ ] **10.6.4 — Space Invaders Mini**: Canvas-based, 60-second arcade session
- [ ] **10.6.5 — Pattern Memory**: Grid-based sequence recall game
- [ ] **10.6.6 — Tangram Builder**: Drag-and-drop shape puzzle with silhouettes
- [ ] **10.6.7 — Reflex Tap**: Reaction time game, 10 rounds
- [ ] **10.6.8 — Word Scramble**: Subject vocabulary unscramble
- [ ] **10.6.9 — Pixel Art Reveal**: Persistent tile-unlock reward image
- [ ] **10.6.10 — Gravity Collector**: Canvas physics collection game
- [ ] **10.6.11 — Mini 2048**: Tile-merging puzzle, short version
- [ ] **10.6.12 — Admin Games page**: `/admin/games` — grid of all games with
      "Preview" button (plays the game) and on/off toggle per game. Toggle state
      stored in settings/config.
- [ ] **10.6.13 — Milestone integration**: Replace current hardcoded Sudoku trigger
      with random selection from enabled games pool

### Tasks (backend)
- [ ] Add `GameConfig` model or settings entry to track enabled/disabled games
- [ ] Add `/admin/games` GET route — renders game grid with toggle controls
- [ ] Add `/admin/games/toggle` POST route — enables/disables a game by ID
- [ ] Add `/api/games/enabled` GET endpoint (optional) — returns enabled game list
      for the milestone trigger

### Tasks (frontend)
- [ ] Create `reward_games.js` with game registry pattern:
      ```
      const GAMES = { sudoku: { name, init, cleanup }, tictactoe: { ... }, ... }
      ```
- [ ] Each game: `init(container, onComplete)` renders into div, calls onComplete
      when done/skipped
- [ ] Generic game modal with skip button, game title, and container div
- [ ] Milestone trigger: pick random enabled game → open modal → play → close
- [ ] Admin games page: card grid with preview + toggle per game
- [ ] Fix Sudoku: ensure grid CSS renders, inputs accept digits 1–4, given cells
      are pre-filled and readonly

### Tasks (individual games — all pure JS)
- [ ] Sudoku: fix existing code, extract into `reward_games.js` module
- [ ] Tic-Tac-Toe: 3×3 grid, X/O turns, simple AI, win/draw detection
- [ ] Space Invaders: canvas, ship movement, bullet firing, alien grid, collision
      detection, 60-second timer, score counter
- [ ] Pattern Memory: grid highlight sequence, replay detection, difficulty scaling
- [ ] Tangram: SVG/canvas shapes, drag + rotate, snap detection, silhouette library
- [ ] Reflex Tap: random positioned circle, timing, 10-round average
- [ ] Word Scramble: word bank from subject vocabulary, anagram shuffle, text input
- [ ] Pixel Art Reveal: tile grid, XP-based unlock tracking (localStorage), reveal
      animation
- [ ] Gravity Collector: canvas physics (simple orbit), star spawning, collection
- [ ] Mini 2048: 4×4 grid, arrow key input, tile merging, score display

### Tests
- [ ] Sudoku puzzle solutions are valid (rows/cols/boxes have 1–4)
- [ ] Game registry returns only enabled games
- [ ] Admin toggle endpoint changes game state
- [ ] Milestone trigger selects from enabled pool only
- [ ] Each game's init function renders without JS errors (smoke test)

### Design notes
- Games are "Brain Reset Rewards" — fun, light, no cognitive overload
- Tangram is the most complex to build (drag/rotate); consider Phase 2 if needed
- Pixel Art Reveal needs localStorage for persistence across sessions
- Word Scramble can reuse skill/template vocabulary from feed_loader
- Space Invaders and Gravity Collector are canvas-based; others are DOM-based
- All games should work on both desktop and tablet (touch + keyboard)


## EPIC 11 — History (Coming Soon) Framework Prep
Goal: Prepare the structure so History can drop in cleanly.

- [ ] Add placeholder subject card + “coming soon”
- [ ] Extend feed spec to allow:
      - timeline assets
      - source interpretation (short extracts we write ourselves)
      - cause/consequence matching
- [ ] Add history renderer primitives:
      - timeline SVG
      - map (simple) for historical geography if needed