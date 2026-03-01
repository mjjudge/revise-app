# ADR 011 — Milestone Celebrations & Easter Eggs

| Field   | Value                        |
|---------|------------------------------|
| Status  | Accepted                     |
| Date    | 2026-03-01                   |
| Epic    | 6.6                         |

## Context

The reward loop (XP + Gold) benefits from emotional "wow" moments that break
the study routine and make reaching milestones feel special.  Anna should
receive a celebration every time she crosses a significant XP threshold, with
the option to play a quick mini-game as a treat.

## Decision

### Milestone Detection

A pure function `detect_milestone(old_xp, new_xp, interval=100)` in
`questions.py` checks whether the user's XP has crossed a 100-point boundary.
Detection happens in the `quest_answer()` route handler — it snapshots
`user.xp` before calling `check_answer()`, then compares after.

The interval (100 XP) is defined as `MILESTONE_INTERVAL` constant.  At
difficulty 2 this is roughly 10 correct first-try answers, giving a celebration
roughly once per quest session or two.

### Celebration Components

1. **Fireworks** — A full-screen `<canvas>` overlay with particle-based
   fireworks.  8 bursts are staggered over ~3 seconds, each spawning 30-50
   particles in random colours with gravity.  The canvas is `pointer-events:
   none` so it doesn't block interaction, and self-removes after the animation
   ends.

2. **Milestone banner** — A glowing card on the result page with a rotating
   congratulatory message (6 titles cycle by milestone number) and a "Play a
   Reward Game!" button.

3. **Mini Sudoku** — A 4×4 Sudoku puzzle (numbers 1-4) in a themed modal.
   6 pre-built puzzles are included, randomly selected.  The player fills
   blanks so every row, column, and 2×2 box contains 1-2-3-4.  Input is
   restricted to digits 1-4.  A "Check" button validates and highlights
   correct/wrong cells.

### Why 4×4 Sudoku?

- Quick to play (under 2 minutes) — doesn't derail the study session
- Exercises logical thinking, complementing maths practice
- Simple enough for KS3 level without being trivially easy
- No external dependencies — 6 puzzles embedded as JS arrays
- 9×9 would be too time-consuming for a reward break

### Message Cycling

`milestone_message(xp)` returns a (title, body) tuple from a list of 6
themed messages.  The index is `(xp ÷ 100 - 1) % 6`, so messages cycle
every 600 XP.

## Consequences

- Zero overhead when no milestone is hit (just an integer comparison)
- Celebrations are purely client-side (canvas + JS) — no server load
- Future mini-games (word search, memory match) can be added alongside Sudoku
  by extending the modal with a game selector
- The 100 XP interval can be tuned via `MILESTONE_INTERVAL` without code changes
- Fireworks and Sudoku are conditionally rendered — `{% if milestone %}` keeps
  the result page lightweight when no milestone occurs
