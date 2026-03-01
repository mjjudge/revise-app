# ADR 006: Charts/Tables Asset Rendering

## Status
Accepted

## Context
Several question templates in chapters 5 and 8 require visual assets — data tables,
line graphs, pie charts, and spinners. We needed a rendering approach that:
- Works without heavy dependencies (no matplotlib, no external image services)
- Produces embeddable output that can be stored alongside the question instance
- Matches the fantasy/adventure theme (realm-purple, gold accents)
- Supports conditional rendering (e.g. spinner only shown when scenario uses a spinner)

## Decision
We render all chart/table assets as **pure inline SVG and HTML** inside a single
Python module (`backend/app/services/assets.py`). Key design choices:

1. **No external dependencies** — SVG is built from string templates using only
   `math` from the stdlib. Tables use Tailwind-styled HTML.

2. **Pre-rendered at generation time** — when a question is generated, all its
   assets are rendered immediately and stored as a single HTML string in the
   `QuestionInstance.assets_html` column. This means assets survive replay without
   re-rendering.

3. **Four asset types supported**:
   - `table` — HTML `<table>` with Tailwind classes, supports `rows_from` (dict
     with labels/counts) and static `rows` with `{param}` expression substitution
   - `chart/line` — SVG line chart (400×250, green line/dots, purple grid)
   - `chart/pie` — SVG pie chart with arc paths and colour legend
   - `chart/spinner` — SVG wheel with coloured sectors, labels, centre dot, arrow

4. **Conditional rendering** via a `when` field on asset specs, evaluated by
   `_eval_when()` which supports simple `==` comparisons on dotted param refs.

5. **Dotted reference resolution** — `_resolve_ref("dataset.x", params)` traverses
   nested dicts/lists to fetch values from generated parameters.

6. **Displayed via Jinja2 `| safe` filter** — the `quest_question.html` template
   renders `{{ question.assets_html | safe }}` inside the question card.

## Consequences
**Pros**
- Zero new dependencies; container stays small and fast to build
- SVGs scale cleanly on all screen sizes (responsive via `max-w-*` classes)
- Theme-consistent visuals without a design tool
- Assets are stored with the question, so review/replay works instantly

**Cons**
- SVG rendering is hand-rolled — adding complex chart types requires more code
- No interactivity (tooltips, hover effects) — acceptable for KS3 maths
- If theme colours change, they must be updated in `assets.py` as well as CSS

**Follow-ups**
- EPIC 6 can add visual regression tests (snapshot SVG output)
- Future chart types (bar, scatter) follow the same pattern
