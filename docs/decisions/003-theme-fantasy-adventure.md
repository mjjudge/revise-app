# ADR 003: Theme — Fantasy / Adventure

## Status
Accepted

## Context
Gamification is core to keeping Anna engaged. We needed a visual and tonal theme
for the UI, quest system, reward language, and overall feel.

## Decision
Adopt a **fantasy / adventure** theme throughout the app:
- Practice sessions are called **Quests**
- Hard questions are **Boss Questions**
- Points are **XP** (experience points)
- Currency is **Gold Coins**
- Streaks and achievements use adventure language (e.g. "3-day streak — Warrior!")
- UI uses a fantasy colour palette (deep purples, golds, emerald greens)
- Greeting rotates between "Anna", "Chibs", and "Chibby"

## Consequences
- All UI copy, colours, and iconography follow the fantasy theme
- Template naming in code stays technical (e.g. `mean_median_mode`); theme is presentation-only
- Can evolve with more RPG elements (character avatar, level-up animations) in later EPICs
- Need to keep it age-appropriate and not too dark — whimsical fantasy, not grimdark
