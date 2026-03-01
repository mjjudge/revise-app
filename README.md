# Revise App (LAN-only)

A small internal-only web app hosted on an Ubuntu machine and accessible only from the home LAN. It helps a child revise KS3-level maths across Chapters 5–8:

- Ch5: Representing and interpreting data (charts, averages, time series, pie charts)
- Ch6: Expressions and formulae (substitution, simplify, like terms)
- Ch7: Calculation and measure (metric, conversions, rounding, BIDMAS, mental/written methods)
- Ch8: Probability (scale, equally likely, mutually exclusive, experimental probability)

## Core principles

- **Copyright-safe**: we do **not** reproduce book pages. Questions are generated from our own templates and parameters.
- **Reliable marking**: deterministic template engine computes the correct answers; OpenAI is used for wording/hints/explanations only.
- **Engaging**: short “quests”, boss questions with charts/tables, points-to-coins reward ledger (pocket money rules parent-controlled).
- **Private**: LAN-only access; optional extra HTTP basic auth at the proxy layer + app-level PIN login.
- **Maintainable**: commit after each EPIC, tests for backend + frontend, docs in `/docs`, and session tracking.

## Architecture

- Backend: **FastAPI** (Python 3.12)
- DB: **SQLite** (file persisted in `./data`)
- Frontend: initially minimal; can be server-rendered with HTMX/Tailwind (recommended)
- Charts/images: generated from data (SVG/PNG), not copied from any book
- OpenAI: question polishing + hint ladder + tutor explanations, never used as the answer key
- Reverse proxy: **Caddy** (container)
- Deployment: **Docker Compose**

## Repository conventions

- `BACKLOG.md` tracks epics/stories/tasks
- `SESSION_STATE.md` tracks current focus, decisions, and next steps
- `AGENTS.md` sets build standards: ask if unsure, never guess, tests required
- All design decisions go in `docs/decisions/`
- Backups go to `./backups/` and are **ignored by git**

## Quick start

1) Copy `.env.example` to `.env` and set `OPENAI_API_KEY`:
   - `cp .env.example .env`

2) Start:
   - `make env-up`

3) Verify:
   - Open `http://<ubuntu-lan-ip>:8088/health`

## Key commands

- `make build` / `make build-backend`
- `make env-up` / `make env-down` / `make restart`
- `make logs`
- `make test`
- `make backup`

## Docs

- `docs/TECH_SPEC.md` — technical specification
- `docs/decisions/` — ADRs / design decisions
