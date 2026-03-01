# QUESTION_FEED_SPEC

This app uses **template-driven** question generation. A template defines:
- what kind of question to generate (mean, BIDMAS, conversions, probability, etc)
- constraints (ranges, counts, rounding rules)
- marking rules (exact, tolerance, equivalence, units)
- asset instructions (table, SVG chart)

The system generates an *instance* by sampling parameters deterministically from a seed, then computes the answer key.

## File locations
- Skill definitions: `backend/app/templates/skills.yaml`
- Templates: `backend/app/templates/templates_ch5_to_ch8.yaml`

## Template format (YAML)
Each template contains:
- id: stable identifier (string)
- chapter: 5|6|7|8
- skill: code from skills.yaml
- difficulty: 1..5 (local scale)
- type: one of:
  - numeric
  - multi_choice
  - short_text
  - order_list
  - grid_fill
- prompt: stem with placeholders
- parameters: how to generate values
- marking: how to validate answers
- solution: deterministic steps or a short worked outline
- assets: optional visuals/tables to render (pie chart, line graph, table)

## Assets
Assets are not images from books. They are generated from data:
- table: rows/columns
- chart: pie/line/bar
Backend renders assets to SVG/PNG deterministically from payload.

## Generation
The backend will:
1) select a template by skill/difficulty
2) sample parameters under constraints (seeded)
3) compute correct answer and accepted forms
4) persist the instance payload (so it can be replayed and reviewed)

## Marking
Supported marking modes:
- exact: exact string/number match
- numeric_tolerance: abs/rel tolerance
- rounding: require dp/sf rules
- set_equivalence: allow multiple valid forms (e.g. fractions)
- unit_required: numeric + unit checking

## OpenAI usage (optional)
OpenAI can be asked to:
- rewrite the prompt in a fun tone
- generate hint ladder based on our worked steps
- explain a mistake based on student's attempt
OpenAI must not be used to decide correctness.