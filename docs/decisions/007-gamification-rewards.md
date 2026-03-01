# ADR 007: Gamification & Rewards System

## Status
Accepted

## Context
The revision app needs gamification to motivate a KS3 student. EPIC 2 introduced basic
per-question XP and gold rewards. EPIC 4 extends this into a complete system with:
- Multi-question quest loops with progress tracking
- Streak bonuses to reward momentum
- A weekly gold earnings cap to control pocket money spend
- A payout ledger so the parent can convert gold to real money

## Decision

### Quest Sessions
A **QuestSession** model tracks a loop of questions:
- **Skill quest**: 8 questions from a single skill
- **Chapter quest**: 10 questions mixed across all skills in a chapter

Flow: `POST /quest/start` → question → answer → result → next → ... → summary.
Questions are generated one at a time. The session tracks completed count, correct
count, XP/gold earned, and which question IDs belong to it.

### Streak Bonuses (within a quest)
Consecutive correct answers (first try) build a streak counter on the quest session:
- **3+ in a row**: XP is multiplied by 1.5× (+50%)
- **5+ in a row**: XP is multiplied by 2× (+100%)
- Wrong answer resets the streak to 0
- Best streak is tracked for the summary screen

### Weekly Gold Cap
Gold earnings are capped per ISO week (Monday–Sunday):
- Default cap: **500 gold/week** (= £10.00 at 2p/gold)
- Admin can change the cap via `POST /admin/settings` (in-memory)
- Enforcement happens in `check_answer()` — gold is clamped to remaining weekly allowance

### Gold → Cash Conversion
- Exchange rate: **1 Gold = 2p** (configurable via `GOLD_TO_PENCE` env var)
- Parent records payouts via `POST /admin/payout` — deducts gold from the kid's balance
- **Payout** model stores: gold_amount, cash_pence, note, created_by, timestamp

### Admin Dashboard
The admin page now shows:
- Live stats: XP, Gold, quests completed, accuracy, total paid out
- Payout form: convert gold to cash with optional note
- Weekly cap control: adjustable input field

### Quest Summary Screen
After completing all questions, the kid sees a summary with:
- Accuracy percentage and rank (Legendary ≥90%, Epic ≥70%, Brave ≥50%, Apprentice <50%)
- XP and Gold earned in the quest
- Best streak achieved
- Play again / chapter / home navigation

## Consequences
**Pros**
- Clear motivational loop: quest → progress bar → streak bonus → summary reward
- Controlled pocket money: weekly cap + parent-controlled payouts
- Simple audit trail via Payout records
- No external dependencies added

**Cons**
- Weekly cap is in-memory only — resets on restart (acceptable for single-user LAN app)
- No daily streak tracking yet (per-session only)
- Exchange rate change requires env var update + restart

**Follow-ups**
- EPIC 5 may add hint penalties (reduces gold reward)
- Daily login streaks could be added in EPIC 6
- Payout history could be exported to CSV for record-keeping
