# QUESTION_FEED_SPEC

This app uses **template-driven** question generation. A template defines:
- what kind of question to generate (mean, BIDMAS, conversions, probability, map skills, weather, etc.)
- constraints (ranges, counts, rounding rules)
- marking rules (exact, tolerance, equivalence, units)
- asset instructions (table, SVG chart, map grid, climograph, etc.)

The system generates an *instance* by sampling parameters deterministically from a seed, then computes the answer key.

## File locations

### Maths (legacy)
- Skill definitions: `backend/app/templates/skills.yaml`
- Templates: `backend/app/templates/templates_ch5_to_ch8.yaml`

### Geography
- Skill definitions: `backend/app/templates/skills_geography.yaml`
- Templates: `backend/app/templates/templates_geography.yaml`

### Future subjects
Follow the pattern: `skills_{subject}.yaml` + `templates_{subject}.yaml`.

---

## Skill format (YAML)

Each skill entry has:

| Field     | Type   | Required | Notes |
|-----------|--------|----------|-------|
| `code`    | string | **yes**  | Dotted lowercase identifier, globally unique |
| `name`    | string | **yes**  | Human-readable skill name |
| `subject` | string | optional | `maths` (default), `geography`, `history`, … |
| `unit`    | string | optional | Groups skills into quests. Maths: `data`, `algebra`, `calculation`, `probability`. Geography: `maps`, `weather`, `climate`, `world`. |
| `chapter` | int    | optional | Legacy maths field (5–8). Auto-maps to subject/unit if those are absent. |

### Subject context rules

- If a skill lacks `subject`, the backend assumes `maths` and derives `unit` from `chapter`.
- When `subject` is present, `unit` should also be set.
- Codes should be prefixed by subject: `stats.*`, `algebra.*`, `calc.*`, `prob.*` (maths); `geog.*` (geography); `hist.*` (history).

---

## Template format (YAML)

Each template contains:

| Field        | Type          | Required | Notes |
|--------------|---------------|----------|-------|
| `id`         | string        | **yes**  | Globally unique stable identifier |
| `skill`      | string        | **yes**  | Must reference a loaded skill code |
| `type`       | QuestionType  | **yes**  | See types below |
| `difficulty`  | int (1–5)    | **yes**  | Local difficulty scale |
| `prompt`     | string        | **yes**  | Stem with `{placeholder}` syntax |
| `parameters` | dict          | **yes**  | Generator specs for values |
| `marking`    | MarkingSpec   | **yes**  | How to validate answers |
| `solution`   | SolutionSpec  | **yes**  | Deterministic worked steps |
| `assets`     | list[Asset]   | optional | Visuals/tables to render |
| `subject`    | string        | optional | Should match `skill.subject` if present |
| `unit`       | string        | optional | Should match `skill.unit` if present |
| `chapter`    | int           | optional | Legacy maths field |
| `calculator` | string        | optional | `"basic"` or `"scientific"` |
| `notes`      | dict          | optional | Metadata |

### Question types

- `numeric` — numeric answer (integer or decimal)
- `multi_choice` — pick one from options
- `short_text` — short free text answer
- `order_list` — order items (click-to-order UI)
- `grid_fill` — label/match grid

### Subject context rules (templates)

- If a template lacks `subject`/`unit`, backend derives them from legacy fields (e.g. maths chapter).
- When both template and referenced skill have `subject`, they must match.
- When both have `unit`, they must match.

---

## Assets

Assets are **generated from data** — never scanned/copied from books.

### Maths asset kinds

| Kind    | Sub-type | Fields | Description |
|---------|----------|--------|-------------|
| `table` | —        | `title`, `columns`, `rows_from` or `rows` | HTML table |
| `chart` | `line`   | `x_from`, `y_from`, `x_labels_from`, `title` | SVG line graph |
| `chart` | `pie`    | `data_from`, `title` | SVG pie chart with legend |
| `chart` | `spinner`| `sectors_from` | SVG spinner wheel |

### Geography asset kinds

| Kind                | Min fields | Description |
|---------------------|------------|-------------|
| `map_grid`          | `grid_size_from`, `points_from`, `show_grid_labels` | OS-style grid map with labelled axes and feature points |
| `compass_rose`      | `style` (`simple_8_point` or `bearing_ring`) | Compass overlay; optionally shows degree markings |
| `scale_bar`         | `ratio_from`, `show_km` | Scale bar from map ratio |
| `contours`          | `contour_map_from`, `mark_point`, `label_some_contours` | Synthetic contour map SVG with optional point marker |
| `cross_section_set` | `options_from`, `label_options` | Set of cross-section profile options (A/B/C/D) for MCQ |
| `synoptic_chart`    | `chart_from`, `show_isobars`, `show_hl` | Weather/pressure map with isobars and H/L labels |
| `climograph`        | `months_from`, `temp_c_from`, `rain_mm_from` | Dual-axis chart (bars = rainfall, line = temperature) |
| `diagram_label`     | `diagram_from`, `show_blank_labels` | Labellable diagram (water cycle, etc.) |
| `world_map_blank`   | `show_label_points`, `label_points_from` | Blank world map with numbered label points |
| `rainfall_diagram`  | `diagram_from` | Relief/convectional/frontal rainfall diagram |
| `cloud_cards`       | `clouds_from`, `style` | Cloud type silhouette cards |
| `matching_cards`    | `left_from`, `right_from`, `shuffle` | Left/right matching panel |
| `symbol_key`        | `symbols_from` | Map symbol → meaning key |

---

## Marking modes

### Maths

| Mode                    | Description |
|-------------------------|-------------|
| `exact_numeric`         | Exact number match |
| `exact_text_normalised` | Case-insensitive, whitespace-normalised text match |
| `numeric_tolerance`     | Absolute tolerance (e.g. ±0.02) |
| `rounding_dp`           | Rounding to specified decimal places |
| `fraction_or_decimal`   | Accept fraction or decimal equivalent |
| `remainder_form`        | Division with remainder (e.g. "7 r 3") |
| `algebra_normal_form`   | Algebraic expression normalisation |
| `order_match`           | Ordered list matching with partial credit |
| `mcq`                   | Multiple choice (single correct) |

### Geography (new)

| Mode             | Description |
|------------------|-------------|
| `gridref_4fig`   | 4-figure grid reference; normalises spaces, validates format |
| `gridref_6fig`   | 6-figure grid reference; normalises spaces, validates format |
| `bearing_3digit` | 3-digit bearing with configurable degree tolerance |
| `grid_match`     | Grid/matching card validation (multiple label pairs) |
| `label_match`    | Diagram label matching (position → label) |

---

## Generation contract

The backend generates a question instance by:

1. Selecting a template by `subject`, `unit`, `skill`, `difficulty` filters.
2. Sampling parameters under constraints (seeded RNG for determinism).
3. Computing the correct answer and accepted forms.
4. Rendering assets to HTML/SVG.
5. Persisting the instance payload:
   - `subject`, `unit`, `skill`
   - `template_id`, `seed`
   - `prompt_rendered`, `assets_html`
   - `correct_json`, `payload_json`

This enables:
- UI to keep subject context (subject stored on instance)
- Progress rollups by subject → unit → skill
- Replay and review of any past question

---

## OpenAI usage (optional)

OpenAI can be asked to:
- Rewrite the prompt in a fun tone
- Generate hint ladder based on our worked steps
- Explain a mistake based on student's attempt

OpenAI must **not** be used to decide correctness.