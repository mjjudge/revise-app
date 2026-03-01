# ADR 017 — Unit Quest Standardisation

**Date:** 2025-03-01
**Status:** Accepted

## Context

Maths has a "Chapter Quest" (10 mixed questions from all skills in a chapter) plus per-skill quests (8 questions). Geography only had per-skill quests. The user wanted the mixed-question quest pattern to become a **standard** for all subjects.

## Decision

1. **QuestSession model** extended with `subject: Optional[str]` and `unit: Optional[str]` fields. `chapter` changed from required `int` to `int` with `default=0` so geography (no chapters) doesn't break.
2. **QuestionInstance.chapter** changed from required `int` to `Optional[int]` to allow null for non-maths subjects.
3. **DB migration** — idempotent `ALTER TABLE ADD COLUMN` for `quest_session.subject` and `quest_session.unit`.
4. **`generate_question()`** and **`_select_template()`** accept `subject`/`unit` params. Priority: `template_id > skill > unit > chapter`.
5. **Unit-based template selection** uses existing `get_templates_by_unit(subject, unit)` — picks a random template from all templates in the unit.
6. **Quest routes** updated:
   - `POST /quest/start` — accepts `subject` and `unit` form params
   - `POST /quest/next` — passes `subject`/`unit` from `QuestSession` to `generate_question`
   - `GET /quest/summary/{id}` — dynamic back-link (unit page / chapter page / home)
7. **UI** — `quest_unit.html` gains a "Unit Quest" button (10 Qs, gold gradient, ⚔️) matching the Chapter Quest pattern. Skill quest forms also pass `subject`/`unit` hidden fields.
8. **Summary page** — dynamic back-link and play-again form include `subject`/`unit`/`chapter` as applicable.

## Consequences

- Any new subject added to the system automatically gets unit quests via the same pattern — just add templates with `subject`/`unit` fields.
- Maths chapter quests remain unchanged (no `subject` field sent from maths forms).
- 9 new tests in `test_unit_quest.py`; 273 total tests passing.
