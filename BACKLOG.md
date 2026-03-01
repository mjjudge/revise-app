# BACKLOG

## EPIC 0 — Repo + Build Foundation
- [ ] Scaffold repo structure (backend, frontend, docs, ops)
- [ ] Docker Compose + Caddy proxy
- [ ] Makefile commands: build/up/down/restart/logs/test/backup
- [ ] Git hygiene: .gitignore includes backups/data/logs
- [ ] Docs: TECH_SPEC, decisions folder, session tracking

## EPIC 1 — MVP App Shell
- [ ] App config + env loading
- [ ] Simple PIN auth (kid/admin)
- [ ] Minimal UI: login → home → start practice
- [ ] Persistent SQLite setup

## EPIC 2 — Template Question Engine (Ch5–8 core)
- [ ] Skill taxonomy + difficulty bands
- [ ] Template interface + registry
- [ ] Implement 8–12 templates spanning chapters 5–8
- [ ] Deterministic answer keys + marking rules
- [ ] Question persistence + attempt logging

## EPIC 3 — Charts/Tables Assets
- [ ] SVG pie chart generator
- [ ] Line graph generator (SVG/PNG)
- [ ] Table rendering component
- [ ] Asset caching + re-render from saved payload

## EPIC 4 — Gamification + Rewards
- [ ] Points model + streak rules + hint penalties
- [ ] Wallet + payout ledger (admin)
- [ ] Quest flow (8–12 Q loop) + summary screen
- [ ] Weekly cap + admin controls

## EPIC 5 — Tutor Mode (OpenAI)
- [ ] Tutor API endpoint (payload + attempt + user question)
- [ ] Prompt rules: age-appropriate, no personal data, don’t jump to answer
- [ ] Hint ladder generation (optional)
- [ ] Logging + safety filters

## EPIC 6 — Quality + Observability
- [ ] Expand tests for templates + marking
- [ ] Add basic structured logging
- [ ] Error pages + retry UX
- [ ] ADRs for design decisions

## EPIC 7 — Hardening (LAN-only, optional)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth
- [ ] Optional Tailscale access