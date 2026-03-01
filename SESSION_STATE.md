# SESSION_STATE

## Current objective
EPIC 5 complete. Tutor Mode (OpenAI) fully implemented and tested.

## Completed this session
- EPIC 5 fully implemented:
  - OpenAI integration via `openai` package (GPT-4o model)
  - Tutor service (tutor.py): get_hint(), explain_mistake(), rewrite_prompt_fun()
  - 3-level hint ladder: nudge → worked step → nearly-the-answer
  - "Ask Professor Quill" mistake explanation on wrong answers
  - Fun question rewrite with caching (QuestionInstance.fun_prompt)
  - Schema: hints_used + fun_prompt fields on QuestionInstance
  - Hint penalty: using any hint halves gold reward
  - Safety: age-appropriate prompts, no personal data, no answer leaks
  - Persona: Professor Quill (friendly, encouraging, British)
  - All API calls logged with prompt + response
  - Error handling: friendly fallback if OpenAI is unavailable
  - Tutor API routes: POST /tutor/hint, /tutor/explain, /tutor/rewrite
  - HTMX integration: hint button on question page, explain button on result page
  - 22 new tutor tests (128 total passing)
  - ADR 008: Tutor Mode — OpenAI Integration

## Decisions made
- UI: HTMX + Tailwind CSS, server-rendered via Jinja2 (ADR 001)
- Auth: 4-digit numeric PIN, two roles (ADR 002)
- Theme: Fantasy / adventure (ADR 003)
- Difficulty: Adaptive, auto-adjusts per skill (ADR 004)
- Template engine: YAML-driven, deterministic, seed-based (ADR 005)
- Asset rendering: Pure inline SVG + HTML, no matplotlib (ADR 006)
- Gamification: Quest loops, streak bonuses, gold cap, payouts (ADR 007)
- Tutor: GPT-4o, 3 hint levels, explain + fun rewrite, halve gold penalty (ADR 008)

## Open questions
- None for current EPICs

## Next actions (EPIC 6)
- [ ] Expand tests for templates + marking
- [ ] Add basic structured logging
- [ ] Error pages + retry UX
- [ ] ADRs for design decisions

## Notes / gotchas
- Dockerfile no longer requires uv.lock (uses uv sync without --frozen)
- Tests require --extra dev flag: uv run --extra dev pytest
- The app auto-seeds users on first startup; delete data/app.sqlite3 to re-seed
- SQLModel relationships require `List["Type"]` from typing (not `list["Type"]`)
- Never store or transmit any book page images/text to OpenAI
- IMPORTANT: Rotate the OpenAI API key -- it was briefly in .env.example (now fixed)
- Keep backups on second drive and outside git
- Schema changes require deleting data/app.sqlite3 before restart
- Weekly gold cap is in-memory only — resets on container restart
- OPENAI_API_KEY must be set in .env for tutor features to work
- Tutor features degrade gracefully if API key is missing or API is down
