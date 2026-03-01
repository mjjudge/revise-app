# ADR 008: Tutor Mode — OpenAI Integration

## Status
Accepted

## Date
2026-03-01

## Context
The app needs a tutor feature to help Anna when she's stuck or gets an answer wrong. We want to use OpenAI (GPT-4o) to provide:
1. Progressive hints during questions (3-level hint ladder)
2. Explanations of mistakes after wrong answers
3. Fun rewrites of question stems to increase engagement

This must follow strict safety and data-minimisation rules.

## Decision

### Model & Provider
- **GPT-4o** via the OpenAI API (configurable via `OPENAI_API_KEY` env var)
- Lazy client initialisation — app works without the key, tutor buttons silently fail with a friendly message

### Three Tutor Features

#### 1. Hint Ladder (3 levels)
- **Level 1 (nudge)**: Identifies the method; no numbers from the working
- **Level 2 (worked step)**: Shows the first step of working
- **Level 3 (nearly there)**: Walks through most of the solution, stops just before the answer
- Max 3 hints per question, tracked via `QuestionInstance.hints_used`
- Each hint costs gold: **using any hint halves the gold reward** for that question

#### 2. Explain Mistake
- Available on wrong answers (button: "Ask Professor Quill")
- Receives: question text, correct answer, student answer, solution steps
- Returns: kind explanation of what likely went wrong + correct method

#### 3. Fun Rewrite
- "Make it fun" button rewrites the question stem in an adventurous tone
- Cached in `QuestionInstance.fun_prompt` — only one API call per question
- Must preserve exact mathematical content (same numbers, same operations)

### Safety Rules (enforced in system prompts)
1. Age-appropriate language (KS3 / Year 8 / age 12-13)
2. No personal data sent to or requested by OpenAI
3. Hints NEVER reveal the final answer (hints 1-2); hint 3 stops just before
4. No copyrighted book content referenced
5. British English spelling
6. Concise responses (max 3-4 sentences for hints, 6 for explanations)
7. All API calls logged (prompt + response) for parental review

### Persona
- Tutor character: **Professor Quill** — friendly, encouraging, British

### Schema Changes
- `QuestionInstance.hints_used: int = 0` — tracks hints consumed
- `QuestionInstance.fun_prompt: str | None = None` — cached fun rewrite

### Gold Penalty
- If `hints_used > 0` at answer time, gold is halved (integer division)
- XP is NOT reduced (we encourage learning)

### Error Handling
- If OpenAI API fails, user sees: "Sorry, Professor Quill is taking a break right now."
- App continues to function; tutor features are optional
- If no API key is set, `_get_client()` raises RuntimeError → caught by `_chat()` → friendly message

## Alternatives Considered
- **No penalty for hints**: Rejected — we want hints to be a learning tool, not a shortcut
- **Lose ALL gold after hint**: Rejected — too punitive, discourages asking for help
- **GPT-4o-mini**: User preferred GPT-4o for higher quality explanations
- **Unlimited hints**: Rejected — 3 is enough; more would essentially give away the answer
- **Server-side hint generation (no AI)**: Could work from solution steps alone, but AI produces much more natural, contextual explanations

## Consequences
- Requires `OPENAI_API_KEY` env var for tutor features to work
- Each hint/explain/rewrite call costs ~$0.005-0.02 (GPT-4o pricing)
- All API calls are logged for parental review
- Schema change: delete `data/app.sqlite3` before restart after this update
