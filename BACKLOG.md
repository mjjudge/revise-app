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


## EPIC 10.6 — Brain Reset Reward Games ✅
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
- [x] **10.6.1 — Fix Mini Sudoku**: Debug and fix existing 4×4 Sudoku so grid
      renders with given numbers, inputs accept digits, and check works correctly
- [x] **10.6.2 — Game framework**: Create `reward_games.js` module with game
      registry, random selection, modal/overlay system, skip button, and completion
      callback. Each game is a self-contained function that renders into a container.
- [x] **10.6.3 — Tic-Tac-Toe**: Implement 3×3 grid with simple AI opponent
- [x] **10.6.4 — Space Invaders Mini**: Canvas-based, 60-second arcade session
- [x] **10.6.5 — Pattern Memory**: Grid-based sequence recall game
- [x] **10.6.6 — Tangram Builder**: Drag-and-drop shape puzzle with silhouettes
- [x] **10.6.7 — Reflex Tap**: Reaction time game, 10 rounds
- [x] **10.6.8 — Word Scramble**: Subject vocabulary unscramble
- [x] **10.6.9 — Pixel Art Reveal**: Persistent tile-unlock reward image
- [x] **10.6.10 — Gravity Collector**: Canvas physics collection game
- [x] **10.6.11 — Mini 2048**: Tile-merging puzzle, short version
- [x] **10.6.12 — Admin Games page**: `/admin/games` — grid of all games with
      "Preview" button (plays the game) and on/off toggle per game. Toggle state
      stored in settings/config.
- [x] **10.6.13 — Milestone integration**: Replace current hardcoded Sudoku trigger
      with random selection from enabled games pool

### Tasks (backend)
- [x] Add `GameConfig` model or settings entry to track enabled/disabled games
- [x] Add `/admin/games` GET route — renders game grid with toggle controls
- [x] Add `/admin/games/toggle` POST route — enables/disables a game by ID
- [x] Add `/api/games/enabled` GET endpoint (optional) — returns enabled game list
      for the milestone trigger

### Tasks (frontend)
- [x] Create `reward_games.js` with game registry pattern:
      ```
      const GAMES = { sudoku: { name, init, cleanup }, tictactoe: { ... }, ... }
      ```
- [x] Each game: `init(container, onComplete)` renders into div, calls onComplete
      when done/skipped
- [x] Generic game modal with skip button, game title, and container div
- [x] Milestone trigger: pick random enabled game → open modal → play → close
- [x] Admin games page: card grid with preview + toggle per game
- [x] Fix Sudoku: ensure grid CSS renders, inputs accept digits 1–4, given cells
      are pre-filled and readonly

### Tasks (individual games — all pure JS)
- [x] Sudoku: fix existing code, extract into `reward_games.js` module
- [x] Tic-Tac-Toe: 3×3 grid, X/O turns, simple AI, win/draw detection
- [x] Space Invaders: canvas, ship movement, bullet firing, alien grid, collision
      detection, 60-second timer, score counter
- [x] Pattern Memory: grid highlight sequence, replay detection, difficulty scaling
- [x] Tangram: SVG/canvas shapes, drag + rotate, snap detection, silhouette library
- [x] Reflex Tap: random positioned circle, timing, 10-round average
- [x] Word Scramble: word bank from subject vocabulary, anagram shuffle, text input
- [x] Pixel Art Reveal: tile grid, XP-based unlock tracking (localStorage), reveal
      animation
- [x] Gravity Collector: canvas physics (simple orbit), star spawning, collection
- [x] Mini 2048: 4×4 grid, arrow key input, tile merging, score display

### Tests
- [x] Sudoku puzzle solutions are valid (rows/cols/boxes have 1–4)
- [x] Game registry returns only enabled games
- [x] Admin toggle endpoint changes game state
- [x] Milestone trigger selects from enabled pool only
- [x] Each game's init function renders without JS errors (smoke test)

### Design notes
- Games are "Brain Reset Rewards" — fun, light, no cognitive overload
- Tangram is the most complex to build (drag/rotate); consider Phase 2 if needed
- Pixel Art Reveal needs localStorage for persistence across sessions
- Word Scramble can reuse skill/template vocabulary from feed_loader
- Space Invaders and Gravity Collector are canvas-based; others are DOM-based
- All games should work on both desktop and tablet (touch + keyboard)


## EPIC 10.7 — "Teach Me" AI Mini-Lessons ✅
Goal: When Anna is stuck on a question or gets one wrong, she can request a short
KS3-style lesson from Professor Quill — like a mini classroom lesson on the topic.
Uses GPT-4o with subject-aware prompts (maths vs geography). No gold penalty
for learning.

### Stories
- [x] **10.7.1 — Lesson service**: Add `generate_lesson()` to tutor service with
      subject-aware system prompts (maths: worked example structure; geography:
      key facts + real-world example structure). 600 max tokens.
- [x] **10.7.2 — Lesson API endpoint**: POST `/tutor/lesson` returns structured
      HTML lesson fragment. Caches in `QuestionInstance.lesson_html` field.
- [x] **10.7.3 — Markdown-to-HTML converter**: `_lesson_to_html()` helper converts
      GPT markdown (bold headings, numbered/bullet lists) to styled HTML.
- [x] **10.7.4 — Question page button**: "📖 I don't understand this — teach me!"
      link below the submit/hint buttons. Opens lesson modal.
- [x] **10.7.5 — Result page button**: "📖 Teach me this topic" button on wrong
      answers alongside "Why was I wrong?" button.
- [x] **10.7.6 — Lesson modal**: Full-screen overlay with loading spinner,
      structured lesson content, "Try the Question" dismiss button.
      Escape key and backdrop click to close.

### Tasks (backend)
- [x] Add `lesson_html: Optional[str]` field to `QuestionInstance` model
- [x] Add `_LESSON_SYSTEM_MATHS` prompt (What is it? → How does it work? →
      Worked Example → Top Tips → Encouragement)
- [x] Add `_LESSON_SYSTEM_GEOGRAPHY` prompt (What is it? → Key Facts →
      Real-World Example → Remember! → Encouragement)
- [x] Add `generate_lesson()` function with subject detection from skill prefix
- [x] Update `_chat()` to accept `max_tokens` parameter (600 for lessons)
- [x] Add POST `/tutor/lesson` route with caching
- [x] Add `_lesson_to_html()` and `_inline_format()` helpers

### Tasks (frontend)
- [x] Add lesson modal HTML to `quest_question.html`
- [x] Add lesson modal HTML to `quest_result.html` (wrong answers only)
- [x] Add `openLessonModal()` / `closeLessonModal()` JS with fetch
- [x] Add "Teach Me" button to question page
- [x] Add "Teach me this topic" button to result page

### Tests
- [x] `generate_lesson` returns string for maths skill
- [x] `generate_lesson` uses geography prompt for `geog.*` skills
- [x] `generate_lesson` uses 600 max tokens
- [x] Lesson system prompts contain required structure headings
- [x] Lesson system prompts contain safety rules
- [x] `_lesson_to_html` converts headings, numbered lists, bullet lists, bold
- [x] POST `/tutor/lesson` returns 200 with HTML content
- [x] Lesson is cached in `lesson_html` field (second call skips OpenAI)
- [x] `lesson_html` field defaults to None
- [x] 13 new tests (431 total)
- [x] ADR 023: Teach Me Mini-Lessons


## EPIC 10.8 — Professor Quill Image Integration (Design Review)

**Goal:** Bring Professor Quill to life with illustrated owl images that appear
at meaningful moments during Anna's learning journey, creating emotional
connection and reinforcing a growth-mindset learning environment.

### Science & Pedagogy

This design draws on three evidence-based principles:

1. **Pedagogical Agents & the Persona Effect** (Lester et al., 1997; Moreno
   et al., 2001) — An animated on-screen character with a consistent
   personality increases learner motivation, perceived helpfulness, and
   willingness to persist through difficulty. The effect is strongest when
   the agent displays *emotional congruence* (matching the learner's
   likely emotional state).

2. **Growth Mindset Feedback** (Dweck, 2006) — Praise should target effort
   and strategy, not raw ability. Quill's celebratory appearances reward
   *streaks* (sustained effort) rather than single correct answers, and
   his concerned appearance after a wrong-answer streak normalises mistakes
   as part of learning rather than failure.

3. **Emotional Design in Multimedia Learning** (Um et al., 2012; Plass
   et al., 2014) — Warm, visually appealing design elements induce
   positive emotions that improve comprehension and transfer. A friendly
   owl character adds warmth without adding extraneous cognitive load.

**Design principle:** Quill appears often enough to feel present, but not so
often that he becomes wallpaper. He should feel like a *companion* who
reacts to what's happening. Every appearance should have a clear emotional
or instructional purpose.

### Available Images (5 existing)

| File | Pose | Mapped to |
|---|---|---|
| `quill_thinking.png` | Owl thinking / pondering | Loading states, hint delivery |
| `quill_teaching1.png` | Owl at a blackboard | Lesson modal (alternates with teaching2) |
| `quill_teaching2.png` | Owl with a pointer | Lesson modal (alternates with teaching1) |
| `quill_super_happy.png` | Owl celebrating | Correct-answer streaks (≥3), milestones, tier-ups |
| `quill_concerned.png` | Owl looking worried | Wrong-answer streaks (≥2), encouragement |

### Additional Quill Images (6 — all created ✅)

| File | Pose | Purpose |
|---|---|---|
| `quill_waving.png` | Friendly wave / greeting | Welcome screen, login, start of a new quest |
| `quill_thumbsup.png` | Thumbs-up / wing-up | Single correct answer ("Nice one!") |
| `quill_reading.png` | Owl reading a book | Fun rewrite loading ("Let me rewrite that…") |
| `quill_proud.png` | Owl with a medal / chest puffed | Quest summary — good rank (Brave / Epic / Legendary) |
| `quill_encouraging.png` | Owl with open wings, warm smile | Wrong answer (single) — "Keep going!" |
| `quill_celebrating.png` | Owl with confetti / party hat | Milestone rewards & reward-game unlock |

### 🐰 Bunny Easter Eggs (6 surprise images)

Anna loves Jellycats — so a friendly bunny companion appears as a rare,
delightful surprise. Each bunny mirrors one of the 6 new Quill poses:

| File | Mirrors | Surprise trigger |
|---|---|---|
| `bunny_waving.png` | `quill_waving` | ~15% chance on login/welcome |
| `bunny_thumbsup.png` | `quill_thumbsup` | ~15% chance on single correct answer |
| `bunny_reading.png` | `quill_reading` | ~15% chance on fun rewrite |
| `bunny_proud.png` | `quill_proud` | ~15% chance on quest summary |
| `bunny_encouraging.png` | `quill_encouraging` | ~15% chance on wrong answer |
| `bunny_celebrating.png` | `quill_celebrating` | ~15% chance on milestone |

**Why ~15%?** Rare enough to feel special (Variable Ratio Reinforcement —
Skinner, 1957). Intermittent, unpredictable rewards are the most
motivating kind. Anna will never know when the bunny will pop up,
which keeps the surprise factor alive session after session.

### Appearance Map (all touchpoints)

| Screen / Moment | Image | Trigger | Emotion |
|---|---|---|---|
| **Login / Welcome** | `quill_waving` | Page load | Warm welcome |
| **Question page — loading spinner** | `quill_thinking` | While question renders | Anticipation |
| **Question page — hint requested** | `quill_thinking` | Hint button clicked | Curiosity |
| **Question page — hint delivered** | `quill_thinking` | Hint HTML shown | Helpfulness |
| **Question page — fun rewrite loading** | `quill_reading` | Rewrite button clicked | Fun |
| **Question page — "Teach Me" loading** | `quill_teaching1` | Lesson spinner | Patience |
| **Lesson modal — content shown** | `quill_teaching1` or `quill_teaching2` | Random choice per load | Authority/trust |
| **Result — correct (no streak)** | `quill_thumbsup` | `result.correct == True` | Encouragement |
| **Result — correct (streak ≥ 3)** | `quill_super_happy` | `quest.streak >= 3` | Celebration |
| **Result — wrong (first/second)** | `quill_encouraging` | `result.correct == False`, wrong streak < 3 | Reassurance |
| **Result — wrong (streak ≥ 3)** | `quill_concerned` | Wrong streak ≥ 3 | Empathy |
| **Result — "Explain" response** | `quill_teaching1` | Explain HTML shown | Teaching |
| **Result — milestone unlocked** | `quill_celebrating` | `milestone is not None` | Excitement |
| **Result — tier up** | `quill_super_happy` | `tier_up == True` | Pride |
| **Quest summary — good rank** | `quill_proud` | Rank = Brave / Epic / Legendary | Pride |
| **Quest summary — low rank** | `quill_encouraging` | Rank = Apprentice | Kindness |
| **Practice Boost banner** | `quill_thinking` | Boost suggestion shown | Motivation |

### Stories

**Story 10.8.1 — Quill Image Component & CSS**
- [ ] Create a reusable `quill-avatar` CSS class (circular frame, soft shadow, subtle bounce-in animation)
- [ ] Support 3 sizes: `quill-sm` (48px), `quill-md` (80px), `quill-lg` (120px)
- [ ] Add speech-bubble CSS for Quill's text (pointed at the owl)
- [ ] Ensure images are lazy-loaded (`loading="lazy"`) for performance
- [ ] Test: images render at correct sizes, no layout shift

**Story 10.8.2 — Wrong-Streak Tracking (Backend)**
- [ ] Add `wrong_streak` field to `QuestSession` model (default 0)
- [ ] Increment `wrong_streak` on incorrect answer; reset to 0 on correct
- [ ] Pass `wrong_streak` to result template context
- [ ] Test: wrong_streak increments and resets correctly
- [ ] Test: wrong_streak appears in template context

**Story 10.8.3 — Question Page Integration**
- [ ] Replace spinner text with `quill_thinking` image + "Professor Quill is thinking…"
- [ ] Show `quill_thinking` beside hint responses (speech-bubble style)
- [ ] Show `quill_teaching1` in lesson modal header (replace 📖 emoji)
- [ ] Show `quill_reading` (or `quill_thinking` fallback) during fun-rewrite loading
- [ ] Test: correct image `src` attributes rendered in question page HTML

**Story 10.8.4 — Result Page Integration**
- [ ] Correct answer (no streak): show `quill_thumbsup` (or `quill_super_happy` fallback)
- [ ] Correct answer (streak ≥ 3): show `quill_super_happy` + "🔥 streak!" text
- [ ] Wrong answer (wrong streak < 3): show `quill_encouraging` (or `quill_concerned` fallback)
- [ ] Wrong answer (wrong streak ≥ 3): show `quill_concerned` + growth-mindset message
- [ ] Milestone unlocked: show `quill_celebrating` (or `quill_super_happy` fallback)
- [ ] Tier up: show `quill_super_happy`
- [ ] Explain response: show `quill_teaching1` beside explanation text
- [ ] Test: correct Quill image rendered for each result scenario

**Story 10.8.5 — Quest Summary Integration**
- [ ] Show `quill_proud` for Brave / Epic / Legendary rank
- [ ] Show `quill_encouraging` for Apprentice rank
- [ ] Add a short Quill speech bubble with rank-appropriate message
- [ ] Test: correct image shown per rank tier

**Story 10.8.6 — Welcome / Login Page**
- [ ] Show `quill_waving` on login page with "Welcome to Revise Quest!"
- [ ] Test: image renders on login page

**Story 10.8.7 — Fallback Handling**
- [ ] All Quill image references use fallback (`quill_thinking` as default)
- [ ] If an image file is missing, gracefully hide (CSS `onerror` handler)
- [ ] All `<img>` tags have `alt="Professor Quill"` for accessibility
- [ ] Test: missing image doesn't break page layout

**Story 10.8.8 — Bunny Easter Eggs 🐰**
- [ ] Implement ~15% random chance to swap eligible Quill images for bunny equivalents
- [ ] Bunny swaps apply to the 6 matching poses only (waving, thumbsup, reading, proud, encouraging, celebrating)
- [ ] Core Quill poses (thinking, teaching1/2, super_happy, concerned) never swap — they're pedagogically important
- [ ] Bunny has its own alt text ("Anna's Bunny Friend") and a subtle sparkle animation on appear
- [ ] Test: bunny images only appear for eligible poses
- [ ] Test: bunny probability is approximately correct

**Implementation Notes:**
- All images already served via `/images/` static mount — no backend route changes needed
- Fallback images (noted above) allow us to ship with the 5 existing images first,
  then swap in the 6 new ones as they're created — no code changes needed for swaps
- Image size: recommend ≤ 150KB per PNG for fast loading; consider WebP conversion later
- Wrong-streak tracking (Story 10.8.2) is the only backend/model change required

### Tests
- [ ] Quill CSS classes render at correct sizes
- [ ] Wrong-streak increments on wrong answer, resets on correct
- [ ] Question page: hint shows `quill_thinking` image
- [ ] Question page: lesson modal shows `quill_teaching` image
- [ ] Result page: correct answer shows appropriate Quill image
- [ ] Result page: wrong answer shows appropriate Quill image
- [ ] Result page: streak ≥ 3 shows `quill_super_happy`
- [ ] Result page: milestone shows celebration Quill
- [ ] Quest summary: rank-appropriate Quill shown
- [ ] Missing image handled gracefully (no broken layout)
- [ ] All Quill images have alt text
- [ ] Bunny images appear only for eligible poses (not thinking/teaching/concerned)
- [ ] Bunny swap probability is ~15%


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