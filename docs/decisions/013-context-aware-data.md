# ADR 013 — Context-Aware Data & Realistic Ranges

| Field   | Value                        |
|---------|------------------------------|
| Status  | Accepted                     |
| Date    | 2026-03-01                   |
| Epic    | Bug fix / UX polish          |

## Context

During live testing, Anna encountered a line graph question about
"temperature at noon" with y-axis values ranging from 40–56.  These
values are plausible in Fahrenheit but nonsensical in Celsius — the UK
unit Anna uses daily.  The root cause was that the template picked the
context label ("temperature", "visitors", "step count") independently
from the data range, so every context shared a single generic y_range
of 10–60.

Additionally, the y-axis had no unit label, making it impossible to
tell what the numbers represented.

## Decision

### 1. Context-bundled scenarios

Replaced the independent `context` (pick_one) + `y_range` with a new
`context_dataset` generator that bundles:

| Field     | Purpose                                |
|-----------|----------------------------------------|
| context   | Human-readable label for the prompt    |
| y_min     | Lower bound of sensible data range     |
| y_max     | Upper bound of sensible data range     |
| unit      | Y-axis unit string (°C, mm, £, etc.)   |
| title     | Chart title matching the context       |

Two scenario pools are defined:

**Weekly scenarios** (Mon–Sat x-axis):
- Daily step count: 2,000–12,000 steps
- Number of visitors: 15–90
- Temperature at noon: 5–25 °C
- Hours of sunshine: 0–14 hours
- Books borrowed: 3–30
- Glasses of water: 2–10

**Monthly scenarios** (Jan–Jun x-axis):
- Monthly rainfall: 20–120 mm
- Ice cream sales: £50–£500
- Library visitors: 80–350
- Average temperature: 2–22 °C
- Electricity usage: 150–500 kWh
- Park visitors: 100–800

### 2. Y-axis unit label

The `_render_line_chart` function now accepts an optional `y_label`
from the asset spec.  When present, it renders a rotated SVG text
element on the left side of the chart axis.

### 3. Dynamic chart titles

Chart titles are resolved from params (e.g. `scenario.title`) rather
than hard-coded strings, so they match the selected context.

### 4. Prompt renderer namespace support

`_render_prompt` now wraps nested dict params in a `_Namespace` object
so `{scenario.context}` works with Python's `str.format_map` attribute
access.

## Consequences

- All line graph questions now produce UK-sensible data with clear units
- Adding new contexts requires only appending to the scenario list
- The `time_series` generator still supports explicit `y_range` for
  non-scenario templates
- 199 tests passing, no regressions
