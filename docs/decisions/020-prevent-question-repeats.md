# ADR 020: Prevent Back-to-Back Question Repeats in Quests

## Status
Accepted

## Context
During testing, the same question template was observed appearing in consecutive positions within a single quest session (e.g. the same map question twice in a row). The `_select_template()` function used `random.choice()` with no memory of recently shown templates, making back-to-back repeats likely when a skill has few templates.

## Decision
Add a **template exclusion mechanism** to the question selection pipeline:

1. **`_exclude_recent(candidates, exclude_ids)`** — filters out templates whose IDs are in the exclude set. Falls back to the full candidate list if filtering would leave zero candidates (graceful degradation when the pool is exhausted).

2. **`_select_template()`** accepts a new `exclude_template_ids: set[str] | None` parameter, applied after difficulty-band filtering but before `random.choice()`.

3. **`generate_question()`** passes `exclude_template_ids` through to `_select_template()`.

4. **`quest_next` API endpoint** builds the exclude set by querying all `QuestionInstance.template_id` values for the current quest's `question_ids` before generating the next question.

The exclusion covers the **entire quest session** (all 8-10 questions), not just the previous one. This maximises variety within a quest. When templates are exhausted, the fallback allows repeats rather than erroring.

## Consequences
- **Pro**: Back-to-back (and broader within-quest) repeats are eliminated when sufficient templates exist.
- **Pro**: Graceful fallback — quests never break even with 1-template skills.
- **Pro**: No schema changes; uses existing `quest_session.question_ids` column.
- **Con**: One extra DB query per `quest_next` call (SELECT template_ids by question IDs) — negligible cost.
- **Follow-up**: Adding more templates per skill continues to improve variety.
