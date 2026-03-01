# SESSION_STATE

## Current objective
Bootstrap environment + scaffold the MVP for a LAN-only revision app (Ch5–8).

## Current decisions
- Stack: FastAPI + SQLite + Caddy + Docker Compose
- Deterministic template engine is source of truth for answers
- OpenAI used only for wording/hints/explanations

## Open questions
- UI approach: server-rendered + HTMX (recommended) vs React
- Reward rules: points→coins exchange rate + weekly cap
- Device targets: iPad + phones + desktop

## Next actions (this session)
- [ ] Bring up stack and confirm /health via Caddy
- [ ] Add config module + env loading
- [ ] Add basic auth endpoints + user table (SQLite)

## Notes / gotchas
- Never store or transmit any book page images/text to OpenAI.
- Keep backups on second drive and outside git.
- Add ADR entries in /docs/decisions for non-trivial changes.