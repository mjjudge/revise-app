# ADR 010 — On-screen Calculator

| Field   | Value                        |
|---------|------------------------------|
| Status  | Accepted                     |
| Date    | 2026-03-01                   |
| Epic    | 6.5                         |

## Context

Several KS3 maths topics (mean, metric conversions, BIDMAS, division, pie
charts, substitution, rounding, probability) allow or require a calculator.
Anna should be able to perform arithmetic on-screen without needing a physical
device or switching apps.

## Decision

### Template-level opt-in

A new optional `calculator` field is added to the `TemplateDef` Pydantic model
in the YAML feed schema.  Accepted values are `"basic"` and `"scientific"`
(currently only `basic` is implemented).  Templates that do not need a
calculator omit the field (defaults to `None`).

16 of 30 templates are tagged with `calculator: basic`:
- Mean (v1/v2), Pie chart (v1/v2), Substitution (v1/v2), Metric conversion
  (v1/v2), Rounding (v1/v2), BIDMAS (v1/v2), Division (v1/v2), Experimental
  probability (v1/v2)

### UI

The calculator renders as a collapsible panel on the question page, toggled by
a 🧮 button.  It provides:

- 4×5 grid: digits 0-9, operators (+, −, ×, ÷), decimal point, clear (C),
  backspace (⌫), equals (=)
- Read-only display showing current expression/result
- **"Copy to answer"** button that transfers the display value into the answer
  input field

The calculator is pure client-side JavaScript.  `calcEquals()` uses
`Function()` constructor for expression evaluation, replacing `×` and `÷` with
`*` and `/`.  All other calculator operations manipulate a display string.

### Routing

`quest.py` imports `get_template_by_id` and passes the `calculator` value
(or `None`) to all three `quest_question.html` render calls.  The template
conditionally renders the calculator panel only when `calculator` is truthy.

## Consequences

- Zero impact on non-calculator questions (field is `None`, panel hidden)
- Future `"scientific"` mode can add sin/cos/sqrt buttons by extending the
  panel conditionally
- No external dependencies — pure JS, no library required
- `Function()` is safe here: the expression string is built entirely from
  button clicks, not user text input
