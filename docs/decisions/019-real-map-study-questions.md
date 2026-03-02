# ADR-019: Real OS Map Study Questions

**Status:** Accepted  
**Date:** 2025-03-02

## Context

The geography curriculum requires students to interpret real Ordnance Survey
(OS) maps — reading symbols, grid references, bearings, contours, and settlement
patterns from actual map extracts rather than synthetic diagrams.

We added a Minsterworth OS map extract (PNG) and needed 18 questions covering
compass directions, symbols, human/physical features, grid references (4- and
6-figure), bearings, relief/contours, and settlement patterns.

## Decisions

### 1. Fixed generator for static questions
A new `fixed` generator returns values as-is with no randomisation. This is
essential for map-study questions where answers are pre-defined by the real map.

### 2. Static image serving
`/images/` is mounted as a StaticFiles directory so the OS map PNG can be served
directly. A new `map_image` asset renderer produces responsive `<img>` tags.

### 3. Gridref tolerance
The `gridref_6fig` marker now supports a `tolerance` parameter (±N on the 3rd
and 6th digits) and multiple accepted references (list of correct values).
This accounts for the practical imprecision of reading a real paper map.

### 4. keyword_any marking mode
A new `keyword_any` mode accepts answers that contain any of a list of accepted
keywords/phrases (case-insensitive substring matching). Useful for short-text
answers where multiple phrasings may be valid.

### 5. Template ID prefix
Minsterworth templates use `minsterworth_*` IDs rather than `geog_*` to clearly
identify place-study content. The quality test was updated to accept both
prefixes for geography templates.

### 6. MCQ over free text for explain questions
Relief interpretation, landform, and settlement pattern questions use MCQ rather
than free-text to enable reliable auto-marking without an LLM marker.

## Consequences

- 18 new templates, 10 new skills, 48 new tests (336 total)
- The `fixed` generator + `map_image` asset pattern is reusable for any future
  place-study (e.g. other OS map extracts)
- Static images are stored in `backend/app/images/` (tracked in git)
