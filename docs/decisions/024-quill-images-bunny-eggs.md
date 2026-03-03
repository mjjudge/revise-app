# ADR 024: Professor Quill Image Integration & Bunny Easter Eggs

## Status
Accepted

## Context
Professor Quill (the AI tutor owl) existed only as text/emoji references
throughout the app. Adding illustrated character images at key emotional
moments creates a stronger pedagogical agent experience (Lester et al.,
1997) and leverages emotional design in multimedia learning (Um et al.,
2012).

Anna loves Jellycats, so a set of bunny images mirrors 6 of the Quill
poses as rare (~15%) surprise Easter eggs — using variable ratio
reinforcement (Skinner, 1957) for maximum delight.

## Decision

### Images
- 11 Quill images (thinking, teaching1/2, super_happy, concerned,
  waving, thumbsup, reading, proud, encouraging, celebrating)
- 6 bunny equivalents (waving, thumbsup, reading, proud, encouraging,
  celebrating)
- Served via existing `/images/` static mount

### Avatar system (CSS + JS)
- `quill-avatar` class: circular frame, gold border, soft shadow
- 3 sizes: `quill-sm` (48px), `quill-md` (80px), `quill-lg` (120px)
- `quill-bounce-in` animation for Quill, `bunny-sparkle` for bunny
- `quillImg(pose, size)` JS helper handles bunny swap logic client-side
- Core poses (thinking, teaching1/2, super_happy, concerned) never swap
- `onerror` handler hides broken images gracefully

### Wrong-streak tracking
- Added `wrong_streak` field to `QuestSession` model
- Incremented on wrong answer, reset on correct
- Passed to result template for conditional Quill display:
  - wrong_streak < 3: `quill_encouraging` (growth mindset)
  - wrong_streak ≥ 3: `quill_concerned` + supportive message

### Touchpoints
- Login: `quill_waving` (or bunny surprise)
- Question page: `quill_thinking` for hints, `quill_reading` for rewrites,
  `quill_teaching1/2` for lessons
- Result page: `quill_thumbsup`/`quill_super_happy`/`quill_encouraging`/
  `quill_concerned` based on correct/wrong + streak
- Milestone: `quill_celebrating` (or bunny surprise)
- Tier-up: `quill_super_happy`
- Quest summary: `quill_proud` or `quill_encouraging` based on rank

## Consequences
- All images lazy-loaded with `onerror` fallback — no performance risk
- 27 new tests (458 total)
- DB schema change: `wrong_streak` column added to `quest_session`
  (requires DB recreate or ALTER TABLE)
