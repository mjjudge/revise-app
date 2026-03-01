# ADR 009 — Quality & Observability

**Status**: Accepted  
**Date**: 2025-07-19  

## Context

After EPICs 0–5 delivered the core feature set, the app lacked:
- Structured logging (output was unformatted print/default logger)
- Themed error pages (raw 404/500 JSON from FastAPI)
- Comprehensive cross-validation of YAML question feeds
- Client-side retry UX for form submission errors
- End-to-end generation tests proving every template round-trips correctly

## Decision

### Structured Logging
- `app/core/logging.py` provides two formatters:
  - **`_JSONFormatter`** (production): single-line JSON with `ts`, `level`, `logger`, `msg`, plus optional extras (`request_id`, `user_id`, `method`, `path`, `status`, `duration_ms`).
  - **`_DevFormatter`** (development): ANSI-coloured human-readable output.
- `setup_logging(env, level)` configures the root logger and quietens noisy libraries (uvicorn.access, httpcore, httpx, openai).
- `RequestLoggingMiddleware` logs every HTTP request with method, path, status, and duration.

### Error Pages
- Custom exception handlers for 404, 500, 403 return a themed `error.html` template with fantasy-styled messaging, status codes, and navigation buttons.
- HTMX `responseError` listener shows a toast notification for failed AJAX requests.

### Retry UX
- Answer input has HTML5 `required` attribute for client-side validation.
- Server-side empty-answer check returns an inline HTMX-swappable error message with red-bordered input, avoiding a full page reload.

### Test Expansion
- **YAML validation**: templates reference valid skills, chapters match, marking modes are supported, solution steps exist, IDs have correct prefixes, difficulty distribution.
- **End-to-end generation**: every template generates, correct answer marks correctly, wrong answer marks incorrectly, deterministic with same seed, different seeds produce different questions.
- **Logging tests**: JSON/Dev formatter output, level override, no duplicate handlers.
- **Error page tests**: 404 returns themed HTML, home link present, health endpoint unaffected, empty answer inline error.

### Bug Fixes Found by E2E Tests
- `mark_rounding_dp`: was reading raw `dp_from_param` (a param name string) instead of the resolved `dp` value — caused `ValueError` on non-numeric input. Fixed to rely on `spec["dp"]` which is resolved by `check_answer`.
- `mark_fraction_or_decimal`: `rounding` field could be `None` from Pydantic model dump, causing `AttributeError`. Fixed with `or {}` fallback.

## Consequences

- 151 tests (up from 128), covering all templates end-to-end.
- Two marking bugs fixed that would have affected production.
- Structured logs enable future log aggregation/alerting.
- Users see friendly themed pages instead of raw errors.
