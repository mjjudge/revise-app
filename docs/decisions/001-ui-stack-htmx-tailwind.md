# ADR 001: UI Stack — HTMX + Tailwind (server-rendered)

## Status
Accepted

## Context
We needed to choose between a JS SPA (React/Vite), vanilla JS, or server-rendered
approach for the frontend. The app targets a single household on LAN, primarily
accessed from iPad, phones, and desktop. The user is a KS3 child; responsiveness
and simplicity matter more than complex client state.

## Decision
Use **Jinja2 templates** served by FastAPI with **HTMX** for dynamic interactions
and **Tailwind CSS** (via CDN) for styling. No separate frontend build step.

Rationale:
- Single codebase — templates live alongside the backend
- No Node.js build pipeline needed in production
- HTMX provides smooth UX (partial page updates, form submissions) without a JS framework
- Tailwind CDN avoids a build step; can move to a build if needed later
- Works well on all target devices (iPad, phone, desktop)

## Consequences
- The `frontend/` directory becomes a thin layer (smoke tests only); templates live in `backend/app/templates/`
- Need `jinja2` and `python-multipart` in backend deps (already have jinja2)
- Future drag-and-drop or rich interactions (EPIC 2 phase 2) may need small JS sprinkles
- If we ever need a full SPA, this can be revisited, but unlikely for this scope
