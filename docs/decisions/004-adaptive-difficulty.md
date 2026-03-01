# ADR 004: Adaptive Difficulty

## Status
Accepted

## Context
We need a difficulty model for the question engine. Options: manual selection,
linear progression, or adaptive. Anna should be challenged but not frustrated.

## Decision
Use **adaptive difficulty** that auto-adjusts based on recent performance:
- Each skill has 3 difficulty bands: `easy`, `medium`, `hard`
- Track a rolling window of the last N attempts per skill
- If accuracy > 80% over the window, step up; if < 50%, step down
- Default starting band: `easy` for new skills, last-used for revisited skills
- Admin can override / lock difficulty per skill if needed

Implementation:
- `difficulty_band` field on each question template
- `current_band` tracked per user per skill in a progress table
- Band adjustment runs after each quest completes

## Consequences
- Template engine must tag every template with a difficulty band
- Need a `user_skill_progress` table from the start (EPIC 2 will populate it)
- More complex than fixed difficulty, but much better UX
- Boss questions always pull from `hard` band regardless of current level
