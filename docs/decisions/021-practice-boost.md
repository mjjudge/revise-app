# ADR-021 — Practice Boost: Extra Rewards for Weak Skills

**Status**: Accepted  
**Date**: 2026-03-02

## Context

Anna gravitates to comfortable, high-accuracy skills to farm gold while avoiding
skills she struggles with. This creates a perverse incentive where the reward
system reinforces avoidance of weak areas rather than encouraging practice.

## Decision

Add a **Practice Boost** multiplier that increases rewards for skills the student
is struggling with, making it more lucrative to practise weak skills.

### Boost qualification

A skill qualifies for Practice Boost when:
- Accuracy ≤60% AND ≥3 attempts (enough data to be meaningful), OR
- The skill's adaptive difficulty band has dropped to 1

### Boost removal (auto-mastery)

A skill's boost is **automatically removed** when:
- Accuracy reaches ≥75% AND ≥5 attempts

This prevents permanent boosting — once the skill has been practised enough, it
graduates back to normal rewards.

### Reward multipliers

| Reward | Normal | Boosted |
|--------|--------|---------|
| Gold (first-try correct) | 1× | 2× |
| XP (any correct) | 1× | 1.5× |

Multipliers are applied **after** streak bonuses but **before** the weekly gold
cap and hint penalty, so all existing safeguards still apply.

### Stacking order

1. Base XP/gold by difficulty
2. Streak bonus (+50% at 3, +100% at 5) — XP only
3. **Practice Boost** (1.5× XP, 2× gold)
4. Hint penalty (halve gold)
5. Weekly gold cap

### UI indicators

- **quest_unit.html**: ⚡💎 badge + gold border on boosted skill cards
- **quest_question.html**: "Practice Boost Active" banner above question
- **quest_result.html**: "Practice Boost! 2× Gold & 1.5× XP" callout on correct answers
- **admin.html**: "⚡ Boosted" badge on Needs Practice skills in Skill Insights

## Implementation

- `get_boosted_skills(db, user_id)` → `set[str]` of boosted skill codes
- `check_answer()` now returns `(attempt, result, is_boosted)` 3-tuple
- No database schema changes — boost status is computed dynamically from
  existing `UserSkillProgress` data

## Consequences

- Positive: Incentivises practising weak skills with tangible bonus
- Positive: Auto-removal prevents permanent inflation
- Positive: Framed positively ("bonus treasure for brave adventurers!")
- Risk: Weekly gold cap mitigates any excessive gold farming
- Note: Parents can still control overall gold flow via weekly cap setting
