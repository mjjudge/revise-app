# TECH_SPEC

## Goal
LAN-only revision web app for KS3 maths Chapters 5-8: stats, algebra, calculation/measure, probability. Gamified practice + tutor explanations.

## Non-goals
- No copying/scanning/re-hosting of book content.
- No open internet exposure by default.

## Design Decisions (see `docs/decisions/` for full ADRs)
- **UI**: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- **Auth**: 4-digit numeric PIN, two roles -- kid + admin (ADR 002)
- **Theme**: Fantasy / adventure -- quests, XP, gold coins, boss questions (ADR 003)
- **Difficulty**: Adaptive -- auto-adjusts per skill based on rolling accuracy (ADR 004)
- **User model**: Single child (Anna, nicknames: Chibs/Chibby) + one admin (parent)

## Components
### Backend (FastAPI)
Responsibilities:
- User + PIN auth (kid/admin) with signed session cookies
- Skill registry (Ch5-8 breakdown)
- Template-driven question generator (deterministic answer key)
- Attempt marking + progress stats
- Reward ledger (XP/gold coins/payouts)
- Tutor endpoint (OpenAI-assisted explanations tied to current question payload)
- Asset generation (charts/tables/images as SVG/PNG)
- Jinja2 template rendering (HTML pages served directly)

### Frontend (server-rendered)
- **HTMX** for dynamic interactions (partial updates, form posts)
- **Tailwind CSS** via CDN for styling
- Fantasy / adventure themed UI
- Simple UX: login PIN -> home -> choose quest -> answer loop -> feedback -> summary
- Mixed input types: MCQ, numeric, ordering, drag/drop (phase 2)
- "Hint ladder": progressively reveal help
- "Ask why": opens tutor panel for explanation
- Responsive: iPad, phone, desktop

### Data storage (SQLite)
- Persistent file mounted at `./data/app.sqlite3`
- SQLModel ORM with Pydantic validation
- Migrations via Alembic once schema stabilises

### Reverse proxy (Caddy)
- Routes :8088 -> backend :8000
- Optional basic auth
- LAN-only enforced primarily by firewall rules on host

## OpenAI usage
- NEVER the answer key.
- Allowed:
  - Rewrite question stem in a fun tone
  - Generate hint ladder aligned to our worked solution
  - Generate explanation for "Ask why?" tied to attempt + payload
- Data minimisation: do not send child's personal details or any book content.

## Backups
- `make backup` writes `./backups/backup-<timestamp>.tgz`
- Backups are NOT committed to git

## Testing
- Backend: pytest smoke + unit tests for templates/marking
- Frontend: Node test harness (expand later) or Playwright (phase 2)

## Initial endpoints (MVP)
- `GET /health`
- `POST /auth/login` (PIN)
- `GET /auth/logout`
- `GET /` (home page -- requires auth)
- `GET /admin` (admin dashboard -- requires admin role)
- `GET /skills`
- `POST /quest/start` (skill mix + difficulty)
- `GET /question/{id}`
- `POST /question/{id}/submit`
- `POST /question/{id}/hint`
- `POST /tutor/explain` (OpenAI)
- `GET /progress`

## Template engine

See `docs/QUESTION_FEED_SPEC.md` for the full contract.

### Data files
- `backend/app/templates/skills.yaml` -- skill taxonomy (15 skills across Ch5-8)
- `backend/app/templates/templates_ch5_to_ch8.yaml` -- template catalogue (30 question types, v1+v2 per skill)

### Template types
- `numeric`, `short_text`, `multi_choice` (rendered as radio buttons), `order_list`, `grid_fill`

### Marking modes
- `exact_numeric`, `exact_text_normalised`, `numeric_tolerance`, `rounding_dp`
- `fraction_or_decimal`, `remainder_form`, `algebra_normal_form`
- `order_match`, `mcq`

### Generation flow
1. Select template by skill + difficulty
2. Sample parameters deterministically from a seed
3. Compute answer_key (never OpenAI)
4. Persist `payload_json` + `correct_json` for replay/review
5. Mark by comparing user answer vs `correct_json` using the template's marking mode

### Asset types
- `table` (rendered from data rows)
- `chart` (pie, line, bar, spinner -- generated SVG/PNG, not book images)

Each template produces:
- question stem
- assets spec (table/chart)
- correct answer (typed)
- marking rules (tolerance/rounding/equivalence)
- worked steps
- difficulty band (easy / medium / hard)

### Skill coverage (Ch5-8)
- Ch5 Stats: mean, median, mode, pie chart angles, line graph interpretation
- Ch6 Algebra: substitution, simplify like terms
- Ch7 Calc/Measure: metric conversion, rounding dp/sf, BIDMAS, written division
- Ch8 Probability: scale ordering, equally likely, mutually exclusive, experimental
