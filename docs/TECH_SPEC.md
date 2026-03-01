# TECH_SPEC

## Goal
LAN-only revision web app for KS3 maths Chapters 5–8: stats, algebra, calculation/measure, probability. Gamified practice + tutor explanations.

## Non-goals
- No copying/scanning/re-hosting of book content.
- No open internet exposure by default.

## Components
### Backend (FastAPI)
Responsibilities:
- User + PIN auth (kid/admin)
- Skill registry (Ch5–8 breakdown)
- Template-driven question generator (deterministic answer key)
- Attempt marking + progress stats
- Reward ledger (points/coins/payouts)
- Tutor endpoint (OpenAI-assisted explanations tied to current question payload)
- Asset generation (charts/tables/images as SVG/PNG)

### Frontend
- Simple UX: choose quest → answer loop → feedback → summary
- Mixed input types: MCQ, numeric, ordering, drag/drop (phase 2)
- “Hint ladder”: progressively reveal help
- “Ask why”: opens tutor panel for explanation

### Data storage (SQLite)
- Persistent file mounted at `./data/app.sqlite3`
- Migrations via Alembic once schema stabilises

### Reverse proxy (Caddy)
- Routes :8088 → backend :8000
- Optional basic auth
- LAN-only enforced primarily by firewall rules on host

## OpenAI usage
- NEVER the answer key.
- Allowed:
  - Rewrite question stem in a fun tone
  - Generate hint ladder aligned to our worked solution
  - Generate explanation for “Ask why?” tied to attempt + payload
- Data minimisation: do not send child’s personal details or any book content.

## Backups
- `make backup` writes `./backups/backup-<timestamp>.tgz`
- Backups are NOT committed to git

## Testing
- Backend: pytest smoke + unit tests for templates/marking
- Frontend: Node test harness (expand later) or Playwright (phase 2)

## Initial endpoints (MVP)
- `GET /health`
- `POST /auth/login` (PIN)
- `GET /skills`
- `POST /quest/start` (skill mix + difficulty)
- `GET /question/{id}`
- `POST /question/{id}/submit`
- `POST /question/{id}/hint`
- `POST /tutor/explain` (OpenAI)
- `GET /progress`

## Template engine
Each template produces:
- question stem
- assets spec (table/chart)
- correct answer (typed)
- marking rules (tolerance/rounding/equivalence)
- worked steps

Examples:
- mean/median/mode from list
- pie chart angles from counts
- time-series line graph interpretation
- substitution into expression (incl negatives)
- simplify like terms
- unit conversion + rounding
- BIDMAS evaluation
- experimental probability from trials