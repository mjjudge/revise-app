# ADR-022: Brain Reset Reward Mini-Games (EPIC 10.6)

## Status
Accepted

## Context
Anna hits milestone celebrations (every 100 XP) that previously triggered only
fireworks and a broken inline Sudoku. We wanted proper reward mini-games as
"Brain Reset Rewards" — fun, lightweight, no penalty, max 90 seconds.

The existing Sudoku was broken due to CSS/JS blocks being wrapped in Jinja2
runtime conditionals (`{% if milestone %}{% block head %}...{% endblock %}{% endif %}`),
which doesn't work reliably in Jinja2 template inheritance (blocks are
compile-time constructs).

## Decision
1. **Game Framework**: Created `backend/app/static/reward_games.js` with a
   game registry pattern. Each game is a self-contained IIFE that registers
   itself via `registerGame(id, name, icon, initFn, cleanupFn)`. Games
   render into a provided container div and call `onComplete()` when done.

2. **10 Games Implemented**:
   - Mini Sudoku (fixed) — 4×4 grid, fill blanks
   - Tic-Tac-Toe — vs simple AI opponent
   - Space Invaders — canvas, 45-second arcade session
   - Pattern Memory — 4×4 grid sequence recall
   - Reflex Tap — tap circles, 10 rounds, average reaction time
   - Word Scramble — unscramble subject vocabulary
   - Mini 2048 — tile-merging, target 256
   - Gravity Collector — canvas physics, collect orbiting stars
   - Tangram Builder — fill shape silhouettes
   - Pixel Art Reveal — tap tiles to reveal pixel art

3. **Admin Games Page**: `/admin/games` with preview buttons and on/off
   toggles per game. Toggle state persists via JSON config file.

4. **Static File Serving**: Added `/static` mount in `main.py` for JS files.

5. **Milestone Integration**: On milestone, a random game is picked from the
   enabled pool. Game list is passed as `enabled_games` in template context.

## Alternatives Considered
- **Separate JS files per game**: More modular but adds HTTP requests. Single
  file is simpler for a LAN app with 10 small games.
- **WebSocket/server-side games**: Overkill. All games are pure client-side JS.
- **DB-backed game config**: A JSON file is simpler for a single-user app.

## Consequences
- 402 tests passing (12 new for game config)
- All styles inline in JS (no separate CSS needed, fixes the Jinja2 block issue)
- Games work on both desktop (keyboard) and tablet (touch/buttons)
- Admin can preview any game and toggle rotation without code changes
