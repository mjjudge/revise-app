# ADR 015: Multi-Subject Navigation & Feed Fields

## Status
Accepted

## Date
2026-03-01

## Context

The app started as Maths-only (KS3 chapters 5–8). We are extending to **Geography**
and later **History**. The current codebase assumes a single subject:

- `SkillDef` requires `chapter: int` (validated 5–8).
- `TemplateDef` requires `chapter: int` (validated 5–8).
- The home page hardcodes four maths chapter cards.
- Routing is `/ → /quest/chapter/{N} → question`.

Multi-subject support requires new top-level fields, a subject dashboard, and
backward-compatible loading of existing maths feeds alongside new geography feeds.

## Decision

### 1. Introduce `subject` and `unit` fields

**Skills** gain optional fields:

| Field     | Type   | Required | Default           |
|-----------|--------|----------|-------------------|
| `subject` | string | optional | `"maths"` (legacy)|
| `unit`    | string | optional | derived from chapter for maths |

**Templates** gain the same optional fields. When both skill and template define
`subject` / `unit`, they must be consistent.

Legacy maths skills/templates that only have `chapter` are auto-mapped:

| Chapter | Subject | Unit          | Display name             |
|---------|---------|---------------|--------------------------|
| 5       | maths   | data          | Data & Charts            |
| 6       | maths   | algebra       | Expressions & Formulae   |
| 7       | maths   | calculation   | Calculation & Measure    |
| 8       | maths   | probability   | Probability              |

Geography skills/templates set `subject: geography` and `unit` explicitly
(maps, weather, climate, world).

### 2. Loader changes

- Load **all** YAML packs from the templates directory:
  - `skills.yaml` + `templates_ch5_to_ch8.yaml` (maths, legacy)
  - `skills_geography.yaml` + `templates_geography.yaml`
  - Future: `skills_history.yaml` + `templates_history.yaml`
- IDs must be globally unique across all loaded template files.
- Cross-validation checks `template.skill ∈ loaded_skills`.
- Subject/unit consistency: if both skill and template specify `subject`,
  they must match; same for `unit`.
- `chapter` remains optional for backward compatibility (required only if
  `subject` is absent — defaults to `maths`).

### 3. Subject-scoped navigation

Post-login flow:

```
Login → Subject Dashboard → Subject Home (units) → Unit Skills → Questions
                ↑                                       |
                └──────── persistent top bar ────────────┘
```

- **Subject Dashboard** (`/`): cards for each subject with progress summary.
- **Subject Home** (`/subject/{subject}`): unit/quest list.
- **Unit Skills** (`/quest/chapter/{chapter}` for maths, `/subject/{subject}/unit/{unit}` for others): skill list.
- **Persistent top bar**: shows current subject, allows switching.
- Questions stay in subject context; "Back" returns to the subject, not the dashboard.

### 4. Progress hierarchy

Progress is rolled up: `subject → unit → skill`.
`QuestionInstance` already stores `skill` and `chapter`; add `subject` column
(nullable, defaulting to `"maths"` for existing rows via migration).

### 5. New marking modes (Geography)

Added to the `MarkingMode` enum when implemented:

- `gridref_4fig` — normalised 4-figure grid reference matching
- `gridref_6fig` — normalised 6-figure grid reference matching
- `bearing_3digit` — 3-digit bearing with degree tolerance
- `grid_match` — label/matching card validation
- `label_match` — diagram label matching

### 6. New asset kinds (Geography)

| Kind               | Description                              |
|--------------------|------------------------------------------|
| `map_grid`         | OS-style grid with labelled axes + points|
| `compass_rose`     | 8-point or bearing-ring compass          |
| `scale_bar`        | Ratio-based scale bar                    |
| `contours`         | Synthetic contour map (SVG)              |
| `cross_section_set`| Set of cross-section profile options     |
| `synoptic_chart`   | Isobar/weather map                       |
| `climograph`       | Dual-axis temperature + rainfall chart   |
| `diagram_label`    | Labellable diagram (water cycle, etc.)   |
| `world_map_blank`  | Blank world map with label points        |
| `rainfall_diagram` | Relief/convectional/frontal diagram      |
| `cloud_cards`      | Cloud type silhouette cards              |
| `matching_cards`   | Left/right matching panel                |
| `symbol_key`       | Map symbol → meaning key                 |

## Consequences

- Feed loader becomes multi-file; caches all skills + templates globally.
- `SkillDef` and `TemplateDef` Pydantic models need `subject` and `unit` as
  optional fields with backward-compatible validators.
- `chapter` validation (5–8 range) only applies when `subject == "maths"`.
- Home page becomes a subject dashboard; existing maths chapter page remains
  largely unchanged but is now reached via `/subject/maths`.
- Geography generators and renderers are a separate EPIC (9); the navigation
  framework (EPIC 8) is subject-agnostic and can go live with maths only,
  showing Geography as "Coming Soon" until generators are implemented.
- History is a placeholder ("Coming Soon" card) until its content pack is ready.
