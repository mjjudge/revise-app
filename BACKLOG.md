# BACKLOG

## EPIC 0 -- Repo + Build Foundation
- [x] Scaffold repo structure (backend, frontend, docs, ops)
- [x] Docker Compose + Caddy proxy
- [x] Makefile commands: build/up/down/restart/logs/test/backup
- [x] Git hygiene: .gitignore includes backups/data/logs
- [x] Docs: TECH_SPEC, decisions folder, session tracking
- [x] Add QUESTION_FEED spec and initial YAML feeds (skills + templates)
- [x] Add YAML validation test to ensure templates reference valid skills and supported marking modes

## EPIC 1 -- MVP App Shell
- [x] App config + env loading (Pydantic Settings)
- [x] Simple PIN auth (kid/admin) with signed session cookies
- [x] User model (SQLModel) + bcrypt PIN hashing + seed on startup
- [x] Jinja2 + HTMX + Tailwind base template (fantasy theme)
- [x] Login page (user selection + 4-digit PIN pad)
- [x] Home page (quest launcher, XP/Gold display, chapter cards)
- [x] Admin dashboard (progress view + reward controls placeholder)
- [x] Backend tests: 14 tests (config, auth flow, health)
- [x] ADRs: 001 UI stack, 002 auth model, 003 theme, 004 adaptive difficulty
- [x] Persistent SQLite setup

## EPIC 2 -- Template Question Engine (Ch5-8 core)
- [x] Skill taxonomy + difficulty bands
- [x] Template interface + registry
- [x] Implement template loader for YAML feeds (skills.yaml + templates_ch5_to_ch8.yaml)
- [x] Validate feed on startup (unique ids, skill exists, chapter match, supported types/marking modes)
- [x] Deterministic generator framework (seeded) to expand template parameters into an instance payload
- [x] Persist generated instance payload_json + correct_json for replay/review
- [x] Implement 8-12 templates spanning chapters 5-8
- [x] Doubled question bank: 15 v2 templates (30 total) with varied difficulty and wording
- [x] Deterministic answer keys + marking rules
- [x] Question persistence + attempt logging
- [x] Adaptive difficulty band adjustment
### EPIC 2 -- Tests
- [x] Tests: template loading + schema validation
- [x] Tests: generator determinism (same seed => same instance)
- [x] Tests: marking modes (numeric tolerance, rounding, fraction/decimal equivalence, remainder form, ordering)

## EPIC 3 -- Charts/Tables Assets
- [x] SVG pie chart generator
- [x] Line graph generator (pure SVG)
- [x] Table rendering component (HTML + Tailwind)
- [x] Spinner renderer (SVG)
- [x] Conditional asset rendering (when expressions)
- [x] Assets wired into question generation + stored in DB
- [x] 12 asset rendering tests
- [x] ADR 006: Charts/Tables Asset Rendering

## EPIC 4 -- Gamification + Rewards
- [x] QuestSession model (8Q skill / 10Q chapter loops)
- [x] Quest flow: start → question → answer → result → next → summary
- [x] Streak bonus: +50% XP at 3 correct, +100% at 5 correct (within quest)
- [x] Weekly gold cap (admin-configurable, default 100)
- [x] Payout model + admin payout API (gold → cash at 2p/gold)
- [x] Admin dashboard: live stats, payout form, reward controls
- [x] Quest summary screen with rank (Legendary/Epic/Brave/Apprentice)
- [x] Config: gold_to_pence, weekly_gold_cap
- [x] 16 gamification tests (106 total)
- [x] ADR 007: Gamification & Rewards System

## EPIC 5 -- Tutor Mode (OpenAI)
- [x] Tutor API endpoint (payload + attempt + user question)
- [x] Prompt rules: age-appropriate, no personal data, don't jump to answer
- [x] Hint ladder generation (3-level: nudge → worked step → nearly-the-answer)
- [x] Fun rewrite of question stems (cached)
- [x] Hint penalty (halves gold reward)
- [x] Logging + safety filters
- [x] 22 tutor tests (128 total)
- [x] ADR 008: Tutor Mode — OpenAI Integration

## EPIC 6 -- Quality + Observability
- [x] Structured logging (JSON prod / coloured dev) with `core/logging.py`
- [x] Request logging middleware (method, path, status, duration_ms)
- [x] Themed error pages (404/500/403) with `error.html`
- [x] HTMX error toast for failed AJAX requests
- [x] Retry UX: HTML5 `required` + server-side empty-answer inline error
- [x] YAML validation tests (skills, chapters, marking modes, solution steps, ID prefixes, difficulty)
- [x] End-to-end template generation tests (generate, mark correct, mark wrong, determinism, seed variety)
- [x] Logging + error page tests
- [x] Bug fixes: `mark_rounding_dp` dp_from_param, `mark_fraction_or_decimal` rounding None
- [x] 23 quality tests (151 total)
- [x] ADR 009: Quality & Observability

## EPIC 7 -- Hardening (LAN-only, optional)
- [ ] UFW rules for LAN subnet
- [ ] Optional Caddy basic auth
- [ ] Optional Tailscale access
