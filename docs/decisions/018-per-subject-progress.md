# ADR 018 — Per-Subject Progress Tracking

**Status:** accepted  
**Date:** 2025-07-15  
**Epic:** 10 — Subject Progress, Levels & Rewards Balancing

## Context

With multiple subjects (maths, geography, future history), progress stats
(XP, quests completed, accuracy, streaks) were only tracked globally on the
`User` model. Parents and students had no visibility into how much effort
went into each subject. The admin dashboard also showed only aggregate stats.

## Decision

Add a **denormalised `SubjectProgress` table** that is incremented in
real-time every time `check_answer()` is called, rather than computing
subject stats from joins across `Attempt` + `QuestionInstance` on every page
load.

### Schema

| Column | Type | Notes |
|---|---|---|
| `id` | int PK | auto |
| `user_id` | FK → user.id | indexed |
| `subject` | str | indexed; `"maths"`, `"geography"`, … |
| `xp_earned` | int | running total |
| `gold_earned` | int | running total |
| `quests_completed` | int | incremented when `quest.finished` |
| `questions_answered` | int | every attempt |
| `questions_correct` | int | first-try correct only |
| `best_streak` | int | high-water mark |
| `last_played` | datetime | updated each answer |

### Subject derivation

The subject code is determined from:
1. `template.subject` (most templates have this set via `derive_subject_unit`)
2. `quest.subject` (set on quest creation)
3. Fallback `"maths"` (legacy maths chapter quests)

### UI changes

- **Home page** (`home.html`): each subject card shows per-subject XP earned
  and quests completed from `subject_stats` dict.
- **Subject home** (`subject_home.html`): stats bar shows subject-specific
  XP, quests done, correct/answered, and best streak instead of globals.
- **Admin dashboard** (`admin.html`): new per-subject breakdown card showing
  XP, gold, quests, accuracy, questions done, best streak per subject.

## Consequences

- **Positive:** Fast O(1) lookups per page load; no complex aggregation queries.
- **Positive:** Easy to add new subjects — just answer questions and the row
  auto-creates.
- **Trade-off:** Denormalised data could drift from source-of-truth (`Attempt`
  table) if bugs occur. Acceptable for a family app; can add a
  `recalculate_subject_progress` admin action later if needed.
- **No migration needed:** New table auto-created by `SQLModel.metadata.create_all`.
