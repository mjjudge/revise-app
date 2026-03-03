# AGENTS (Build Standards)

## Core rules
1) **Ask if unsure. Never guess.**
2) **Commit after every EPIC** (and optionally per major story), with a clear message.
3) **Write tests** for backend and frontend for any non-trivial logic.
4) **No copyrighted book content**: do not add scanned pages, copied questions, or transcribed passages to the repo.
5) **All decisions documented**: create an entry in `docs/decisions/` for:
   - architectural changes
   - schema decisions
   - reward rules
   - OpenAI prompt policy
6) Keep `SESSION_STATE.md` updated at the end of each working session:
   - what changed
   - decisions made
   - next actions
7) **NEVER delete `data/app.sqlite3`** to fix schema issues. User progress (XP, gold, quest history) lives there and cannot be recreated. Instead, use `ALTER TABLE … ADD COLUMN` or wait until the lightweight DB migration (BACKLOG) is implemented.

## File locations
- Specs and decisions: `docs/`
- ADRs: `docs/decisions/NNN-<title>.md`
- Backlog: `BACKLOG.md`
- Session tracking: `SESSION_STATE.md`
- Ops/deploy: `ops/`

## Testing expectations
- Backend: pytest (unit tests for templates/marking; API smoke tests)
- Frontend: at minimum node test harness; later Playwright for UI flows
- CI-ready: ensure `make test` runs cleanly

## Makefile contract
- `make env-up` must bring the app up in a fresh clone (after `.env` is set)
- `make backup` must create a timestamped archive in `./backups/` (ignored by git)
- `make restart` must be safe and idempotent