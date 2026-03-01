# ADR 002: Auth Model — Simple PIN with two roles

## Status
Accepted

## Context
The app runs on a home LAN for a single family. We need minimal auth to separate
the child experience from admin (parent) controls. Full user management, OAuth, or
passwords are overkill.

## Decision
- **Two users**: one child (Anna), one admin (parent)
- **4-digit numeric PIN** for each, stored hashed (bcrypt) in the users table
- **Session cookie** (signed, HTTP-only) after successful login
- **Roles**: `kid` and `admin`
- No username entry — user taps their avatar/name on a selection screen, then enters PIN
- PINs are seeded on first run via a startup script / env vars

## Consequences
- Simple and iPad-friendly (numeric keypad for PIN)
- No password reset flow needed — admin can update PINs directly in DB or via admin UI
- If more children are added later, we add rows to the users table + a selector screen
- LAN-only + optional Caddy basic auth provides the outer security layer
