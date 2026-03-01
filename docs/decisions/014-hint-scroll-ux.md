# ADR 014 — Hint Button Scroll-to-Top UX

| Field   | Value                        |
|---------|------------------------------|
| Status  | Accepted                     |
| Date    | 2026-03-01                   |
| Epic    | UX polish                    |

## Context

During live testing, Anna opened the on-screen calculator (at the
bottom of the question card) and then tapped "Hint".  The hint content
rendered in the `#hint-area` div near the top of the question card, but
because the calculator had pushed the viewport down, the hint appeared
off-screen above the fold.  Anna didn't notice the hint had loaded.

## Decision

Add `scrollIntoView({behavior: 'smooth', block: 'center'})` on the
`#hint-area` element after the hint button is clicked.  This is wired
in two places:

1. **Initial hint button** (`quest_question.html`): An `onclick`
   handler with a 300ms delay (to let the HTMX response render) scrolls
   the hint area into the centre of the viewport.

2. **"Next Hint" button** (server-rendered in `tutor.py`): The same
   scroll behaviour is applied to the progressive hint buttons (hint
   2/3 and 3/3) so the user always sees the new hint content.

### Why not `hx-on::after-settle`?

HTMX's `hx-on::after-settle` could target the swap event more
precisely, but putting it on a nested f-string inside `tutor.py` adds
escaping complexity.  A simple `onclick + setTimeout(300ms)` is
reliable, predictable, and easy to maintain.

## Consequences

- Hints are always visible regardless of scroll position
- Smooth scroll animation provides clear visual feedback
- No additional JS dependencies
- Works on all browsers (Safari, Chrome, Firefox)
