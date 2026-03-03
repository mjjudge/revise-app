# ADR 025 — Tangram: Flip, Centre & Solid Silhouette

**Status**: Accepted  
**Date**: 2025-07-12

## Context

The tangram puzzle editor and game had three usability issues:

1. **No flip/mirror** — the parallelogram is the only non-symmetrical piece. Without
   flipping, some target shapes are impossible to build.
2. **No centring** — the admin had to manually drag all pieces to visually centre a
   design in the play area before saving.
3. **Visible internal lines** — the target silhouette drew each piece as a separate
   SVG polygon with its own stroke. Where pieces shared edges, internal seam lines
   were visible, effectively revealing the solution layout.

## Decision

### Flip
- Added a "↔ Flip" button to both the **editor** and the **game**.
- Flip applies an SVG `scale(-1,1)` transform to the piece group, mirroring it
  horizontally around its local origin.
- The `flipped` boolean is stored in `startPose` and `targetPose` in the puzzle JSON.
- `checkSnap()` now requires `p.flipped === slot.flipped` — the piece must be in the
  correct flip state to lock into position.
- The `DEFAULT_RULES.allowFlip` flag already existed as `false`; it remains available
  for future per-puzzle restriction, but flipping is now always exposed in the UI.

### Centre
- Added a "⊞ Centre" button to the **editor**.
- Computes the world-space bounding box of all 7 pieces (accounting for rotation and
  flip) and shifts every piece so the bounding box is centred within the PLAY area
  (300 × 280, offset 50,10).

### Solid Silhouette
- Replaced per-piece ghost `<polygon>` elements with a **single compound `<path>`**.
- Each piece's polygon vertices are transformed to world coordinates (applying
  position, rotation, and flip), then concatenated into one SVG path string
  (`M…L…Z M…L…Z …`).
- The path is filled with a uniform semi-transparent colour and `fill-rule: nonzero`,
  overlapping regions merge visually (no internal edges).
- A second copy of the same path is drawn with a subtle stroke for the outer border.

## Consequences

- Existing puzzle JSON files without `flipped` fields work fine — `!!undefined` is `false`.
- New puzzles created via `blank_puzzle()` include `flipped: false` in all poses.
- 5 new backend tests added (total 463 after this commit).
- Admin instructions updated to mention Flip and Centre.
