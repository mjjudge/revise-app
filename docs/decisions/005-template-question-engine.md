# ADR 005: Template Question Engine Architecture

**Status:** Accepted  
**Date:** 2026-03-01

## Context
EPIC 2 requires a system to generate maths questions deterministically from YAML
templates, mark student answers, and adapt difficulty over time.

## Decision
We adopted a **template-driven, seed-based architecture** with these components:

1. **YAML Feeds** — skill definitions (`skills.yaml`) and question templates
   (`templates_ch5_to_ch8.yaml`) with Pydantic validation on startup.

2. **Deterministic Generators** — seeded RNG produces identical output for a given
   seed value. Generator functions are registered by name and dispatched via spec.

3. **Marking Engine** — 9 marking modes (exact_numeric, exact_text_normalised,
   numeric_tolerance, rounding_dp, fraction_or_decimal, remainder_form,
   algebra_normal_form, order_match, mcq). Each mode returns a `MarkResult`
   with correct/score/feedback/expected.

4. **Answer Computation** — deterministic answer-key computed from generated
   parameters, keyed by skill type (not by calling OpenAI).

5. **Adaptive Difficulty** — `UserSkillProgress` model tracks per-skill band
   (1-5). Levels up after 3 consecutive correct; levels down on wrong answer.

6. **Rewards** — XP/Gold scaled by difficulty band. Full reward for first attempt,
   half XP for second, nothing for third+.

## Consequences
- All questions reproducible (seed + template_id = exact replay).
- No network calls for generation or marking.
- Adding new templates = adding YAML entries + possibly new generators.
- OpenAI reserved for optional hint/explanation features (EPIC 5+).
