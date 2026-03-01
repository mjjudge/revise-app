# ADR 016 – Geography Content Pack (EPIC 9)

**Status:** Accepted  
**Date:** 2025-07-15

## Context

With maths fully operational (30 templates, 18 generators, 9 marking modes), we need
to add the first non-maths subject: KS3 Geography.  The existing architecture must
support a second subject without breaking maths, using the same template → generator
→ renderer → marking pipeline.

## Decision

### Templates (24 geography templates across 7 categories)

| Category | Count | Question Type | Marking Mode |
|---|---|---|---|
| Knowledge MCQ | 4 | `multi_choice` | `mcq` |
| Matching / Grid-fill | 6 | `grid_fill` | `grid_match` |
| Scale calculations | 2 | `numeric` | `numeric_tolerance` |
| Map / Grid reference | 4 | mixed | `mcq`/`gridref_4fig`/`gridref_6fig`/`bearing_3digit` |
| Contour questions | 3 | mixed | `numeric_tolerance`/`mcq` |
| Climate graph | 3 | mixed | `numeric_tolerance`/`mcq` |
| Weather diagrams | 2 | `multi_choice` | `mcq` |

### New Generator Registry Entries (~15 generators)

- `pick_one` / `pick_one_distinct` — generic list pickers
- `from_object` — extract nested field from context
- `geog_knowledge_mcq` — knowledge MCQ from topic pools
- 6 matching-set generators (instruments, air masses, clouds, map symbols, water cycle, continents/oceans)
- `map_scale` — map ratio picker
- `grid_map_with_features` — SVG grid map with grid references
- `compass_direction_mcq` — compass direction MCQ
- `climograph_dataset` — 12-month climate data across 5 profiles
- `climate_compare_mcq` — compare two climate graphs
- `synthetic_contour_map` — elliptical contour generator
- `isobar_chart_data` / `rainfall_diagram_data` — weather chart data

### New Asset Renderers (9 SVG renderers)

- `matching_cards` — two-column matching layout
- `map_grid` — grid map with labeled feature points
- `compass_rose` — 8-point compass
- `scale_bar` — alternating color bar with km labels
- `climograph` — dual-axis (temp line + rainfall bars)
- `contours` — elliptical contour rings with marked points
- `cross_section_set` — 2×2 profile grid
- `synoptic_chart` — pressure map with H/L centers
- `rainfall_diagram` — 3 distinct rainfall type diagrams

### New Marking Modes (5 modes)

- `gridref_4fig` — strips spaces, validates 4 digits
- `gridref_6fig` — strips spaces, validates 6 digits
- `bearing_3digit` — tolerance-based (±2° default)
- `grid_match` — JSON mapping comparison with partial credit
- `label_match` — alias for grid_match

### New UI: Grid-fill Question Type

A new question input type using `<select>` dropdowns for matching left items to
right items.  Student answer is a JSON mapping sent as a hidden field.

### Navigation

- Geography added to `_SUBJECT_META` in pages.py with 4 units
- Home page Geography card now active (no longer "Coming Soon")
- New `/quest/unit/{subject}/{unit}` route for unit-based skill selection  
- New `quest_unit.html` template with breadcrumb navigation

## Consequences

- 264 tests pass (56 new geography tests + 208 existing)
- Architecture proven extensible to non-maths subjects
- Grid-fill UI pattern reusable for any matching/labelling question
- Geography uses unit-based routing (no chapters)
