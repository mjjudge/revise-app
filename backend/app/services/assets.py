"""Asset rendering — generates SVG charts and HTML tables from question data.

Supports:
- table: HTML table from rows/columns
- chart (line): SVG line chart
- chart (pie): SVG pie chart  (not yet in templates but ready)
- chart (spinner): SVG spinner/wheel
"""

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_assets(asset_specs: list[dict], params: dict[str, Any]) -> list[dict]:
    """Render all asset specs for a question instance.

    Returns list of dicts: {id, kind, html} where html is the rendered
    SVG or HTML string ready to embed.
    """
    rendered = []
    for spec in asset_specs:
        # Check conditional rendering
        when = spec.get("when")
        if when and not _eval_when(when, params):
            continue

        kind = spec.get("kind", "")
        asset_id = spec.get("id", "asset")

        if kind == "table":
            html = _render_table(spec, params)
        elif kind == "chart":
            chart_type = spec.get("chart_type", "line")
            if chart_type == "line":
                html = _render_line_chart(spec, params)
            elif chart_type == "pie":
                html = _render_pie_chart(spec, params)
            elif chart_type == "spinner":
                html = _render_spinner(spec, params)
            else:
                html = f'<p class="text-realm-purple-300">Unsupported chart type: {chart_type}</p>'
        # ── Geography asset kinds ──────────────────────────────
        elif kind == "matching_cards":
            html = _render_matching_cards(spec, params)
        elif kind == "map_grid":
            html = _render_map_grid(spec, params)
        elif kind == "compass_rose":
            html = _render_compass_rose(spec, params)
        elif kind == "scale_bar":
            html = _render_scale_bar(spec, params)
        elif kind == "climograph":
            html = _render_climograph(spec, params)
        elif kind == "contours":
            html = _render_contours(spec, params)
        elif kind == "cross_section_set":
            html = _render_cross_section_set(spec, params)
        elif kind == "synoptic_chart":
            html = _render_synoptic_chart(spec, params)
        elif kind == "rainfall_diagram":
            html = _render_rainfall_diagram(spec, params)
        elif kind == "map_image":
            html = _render_map_image(spec, params)
        else:
            html = f'<p class="text-realm-purple-300">Unsupported asset kind: {kind}</p>'

        rendered.append({"id": asset_id, "kind": kind, "html": html})

    return rendered


# ---------------------------------------------------------------------------
# Conditional evaluation
# ---------------------------------------------------------------------------

def _eval_when(when: str, params: dict[str, Any]) -> bool:
    """Evaluate a simple when condition like "scenario.object_name == 'spinner'"."""
    try:
        parts = when.split("==")
        if len(parts) != 2:
            return True  # can't parse, show anyway

        lhs = parts[0].strip()
        rhs = parts[1].strip().strip("'\"")

        val = _resolve_ref(lhs, params)
        return str(val) == rhs
    except (KeyError, TypeError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Reference resolver
# ---------------------------------------------------------------------------

def _resolve_ref(ref: str, params: dict[str, Any]) -> Any:
    """Resolve a dotted reference like 'dataset.x' from params."""
    parts = ref.split(".")
    val: Any = params
    for p in parts:
        if isinstance(val, dict):
            val = val[p]
        elif isinstance(val, list):
            val = val[int(p)]
        else:
            val = getattr(val, p, None)
    return val


def _resolve_or_literal(ref: str, params: dict[str, Any]) -> Any:
    """Resolve a ref or return its literal value if not a dotted path."""
    if "." in ref:
        try:
            return _resolve_ref(ref, params)
        except (KeyError, TypeError, IndexError, AttributeError):
            return ref
    if ref in params:
        return params[ref]
    return ref


# ---------------------------------------------------------------------------
# Table renderer
# ---------------------------------------------------------------------------

def _render_table(spec: dict, params: dict[str, Any]) -> str:
    """Render an HTML table asset."""
    title = spec.get("title", "")
    columns = spec.get("columns", [])
    rows_from = spec.get("rows_from")
    rows_static = spec.get("rows")

    rows: list[list[str]] = []

    if rows_from:
        # Resolve from params (e.g. "categories" → labels + counts)
        data = _resolve_or_literal(rows_from, params)
        if isinstance(data, dict):
            labels = data.get("labels", [])
            counts = data.get("counts", [])
            for label, count in zip(labels, counts):
                rows.append([str(label), str(count)])
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    rows.append([str(v) for v in item])
                else:
                    rows.append([str(item)])
    elif rows_static:
        for row in rows_static:
            rendered_row = []
            for cell in row:
                rendered_row.append(_render_cell(str(cell), params))
            rows.append(rendered_row)

    # Build HTML
    lines = []
    lines.append('<div class="my-4">')
    if title:
        lines.append(f'  <p class="text-sm text-realm-purple-300 mb-2 font-semibold">{title}</p>')
    lines.append('  <table class="w-full border-collapse rounded-lg overflow-hidden">')

    # Header
    if columns:
        lines.append('    <thead>')
        lines.append('      <tr class="bg-realm-purple-600/60">')
        for col in columns:
            lines.append(f'        <th class="px-4 py-2 text-left text-sm font-semibold text-realm-gold-400">{col}</th>')
        lines.append('      </tr>')
        lines.append('    </thead>')

    # Body
    lines.append('    <tbody>')
    for i, row in enumerate(rows):
        bg = "bg-realm-purple-800/40" if i % 2 == 0 else "bg-realm-purple-800/20"
        lines.append(f'      <tr class="{bg}">')
        for cell in row:
            lines.append(f'        <td class="px-4 py-2 text-sm text-white">{cell}</td>')
        lines.append('      </tr>')
    lines.append('    </tbody>')

    lines.append('  </table>')
    lines.append('</div>')

    return "\n".join(lines)


def _render_cell(cell_str: str, params: dict[str, Any]) -> str:
    """Render a cell value, substituting {param} references."""
    import re

    def _replace(m):
        expr = m.group(1).strip()
        # Handle simple expressions like "trials - successes"
        if " - " in expr:
            parts = expr.split(" - ")
            try:
                a = int(_resolve_or_literal(parts[0].strip(), params))
                b = int(_resolve_or_literal(parts[1].strip(), params))
                return str(a - b)
            except (ValueError, TypeError):
                return expr
        # Simple reference
        val = _resolve_or_literal(expr, params)
        return str(val)

    return re.sub(r"\{(.+?)\}", _replace, cell_str)


# ---------------------------------------------------------------------------
# Line chart renderer (SVG)
# ---------------------------------------------------------------------------

_CHART_W = 400
_CHART_H = 250
_PAD_L = 50
_PAD_R = 20
_PAD_T = 30
_PAD_B = 50


def _render_line_chart(spec: dict, params: dict[str, Any]) -> str:
    """Render an SVG line chart."""
    title_raw = spec.get("title", "")
    title = _resolve_or_literal(title_raw, params) if title_raw else ""
    if not isinstance(title, str):
        title = str(title)

    # Resolve optional y-axis unit label
    y_label_raw = spec.get("y_label", "")
    y_label = _resolve_or_literal(y_label_raw, params) if y_label_raw else ""
    if not isinstance(y_label, str):
        y_label = str(y_label)

    # Resolve x and y data
    x_ref = spec.get("x", "")
    y_ref = spec.get("y", "")
    x_labels = _resolve_or_literal(x_ref, params)
    y_values = _resolve_or_literal(y_ref, params)

    if not isinstance(x_labels, list) or not isinstance(y_values, list):
        return '<p class="text-realm-purple-300">Chart data unavailable.</p>'

    n = min(len(x_labels), len(y_values))
    if n == 0:
        return '<p class="text-realm-purple-300">No data points.</p>'

    y_min = min(y_values[:n])
    y_max = max(y_values[:n])
    y_range = y_max - y_min or 1

    # Plot area
    plot_w = _CHART_W - _PAD_L - _PAD_R
    plot_h = _CHART_H - _PAD_T - _PAD_B

    def px(i: int) -> float:
        return _PAD_L + (i / max(n - 1, 1)) * plot_w

    def py(v: float) -> float:
        return _PAD_T + plot_h - ((v - y_min) / y_range) * plot_h

    lines = []
    lines.append(f'<div class="my-4 flex justify-center">')
    lines.append(f'<svg viewBox="0 0 {_CHART_W} {_CHART_H}" class="w-full max-w-md" xmlns="http://www.w3.org/2000/svg">')

    # Background
    lines.append(f'  <rect width="{_CHART_W}" height="{_CHART_H}" fill="#3b0f7a" rx="8"/>')

    # Title
    if title:
        lines.append(f'  <text x="{_CHART_W / 2}" y="18" text-anchor="middle" fill="#f6b935" font-size="12" font-weight="bold">{title}</text>')

    # Y-axis unit label (rotated, left side)
    if y_label:
        lines.append(
            f'  <text x="12" y="{(_PAD_T + _CHART_H - _PAD_B) / 2}" '
            f'text-anchor="middle" fill="#b89aff" font-size="10" '
            f'transform="rotate(-90, 12, {(_PAD_T + _CHART_H - _PAD_B) / 2})">'
            f'{y_label}</text>'
        )

    # Grid lines + Y labels
    n_grid = 5
    for i in range(n_grid + 1):
        y_val = y_min + (y_range * i / n_grid)
        y_pos = py(y_val)
        lines.append(f'  <line x1="{_PAD_L}" y1="{y_pos}" x2="{_CHART_W - _PAD_R}" y2="{y_pos}" stroke="#6d28d9" stroke-width="0.5"/>')
        lines.append(f'  <text x="{_PAD_L - 5}" y="{y_pos + 4}" text-anchor="end" fill="#b89aff" font-size="10">{int(y_val)}</text>')

    # Line path
    points = " ".join(f"{px(i)},{py(y_values[i])}" for i in range(n))
    lines.append(f'  <polyline points="{points}" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')

    # Data points + X labels
    for i in range(n):
        cx, cy = px(i), py(y_values[i])
        lines.append(f'  <circle cx="{cx}" cy="{cy}" r="4" fill="#34d399" stroke="#ecfdf5" stroke-width="1.5"/>')
        # X label
        lines.append(f'  <text x="{cx}" y="{_CHART_H - 10}" text-anchor="middle" fill="#b89aff" font-size="10">{x_labels[i]}</text>')

    lines.append('</svg>')
    lines.append('</div>')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pie chart renderer (SVG)
# ---------------------------------------------------------------------------

_PIE_R = 90
_PIE_CX = 150
_PIE_CY = 130
_PIE_COLOURS = ["#7c3aed", "#f59e0b", "#10b981", "#ef4444", "#3b82f6", "#ec4899", "#14b8a6", "#f97316"]


def _render_pie_chart(spec: dict, params: dict[str, Any]) -> str:
    """Render an SVG pie chart."""
    title = spec.get("title", "")

    # Resolve data
    data_ref = spec.get("data_from", spec.get("rows_from", ""))
    data = _resolve_or_literal(data_ref, params) if data_ref else {}

    labels = data.get("labels", []) if isinstance(data, dict) else []
    counts = data.get("counts", []) if isinstance(data, dict) else []
    total = sum(counts) if counts else 1

    if not labels or not counts:
        return '<p class="text-realm-purple-300">Pie chart data unavailable.</p>'

    lines = []
    lines.append('<div class="my-4 flex justify-center">')
    lines.append(f'<svg viewBox="0 0 300 280" class="w-full max-w-xs" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="300" height="280" fill="#3b0f7a" rx="8"/>')

    if title:
        lines.append(f'  <text x="150" y="20" text-anchor="middle" fill="#f6b935" font-size="12" font-weight="bold">{title}</text>')

    angle = -90  # start from top
    for i, (label, count) in enumerate(zip(labels, counts)):
        sweep = (count / total) * 360
        colour = _PIE_COLOURS[i % len(_PIE_COLOURS)]

        start_rad = math.radians(angle)
        end_rad = math.radians(angle + sweep)

        x1 = _PIE_CX + _PIE_R * math.cos(start_rad)
        y1 = _PIE_CY + _PIE_R * math.sin(start_rad)
        x2 = _PIE_CX + _PIE_R * math.cos(end_rad)
        y2 = _PIE_CY + _PIE_R * math.sin(end_rad)

        large_arc = 1 if sweep > 180 else 0

        path = (
            f"M {_PIE_CX},{_PIE_CY} "
            f"L {x1},{y1} "
            f"A {_PIE_R},{_PIE_R} 0 {large_arc} 1 {x2},{y2} Z"
        )
        lines.append(f'  <path d="{path}" fill="{colour}" stroke="#3b0f7a" stroke-width="1"/>')

        # Label in legend
        ly = 250 + i * 0  # we'll do legend below
        angle += sweep

    # Legend
    legend_y = _PIE_CY + _PIE_R + 20
    cols = min(len(labels), 4)
    col_w = 280 / cols
    for i, (label, count) in enumerate(zip(labels, counts)):
        colour = _PIE_COLOURS[i % len(_PIE_COLOURS)]
        lx = 10 + (i % cols) * col_w
        ly = _PIE_CY + _PIE_R + 18 + (i // cols) * 16
        lines.append(f'  <rect x="{lx}" y="{ly}" width="10" height="10" fill="{colour}" rx="2"/>')
        lines.append(f'  <text x="{lx + 14}" y="{ly + 9}" fill="#d4c4ff" font-size="10">{label} ({count})</text>')

    lines.append('</svg>')
    lines.append('</div>')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Spinner renderer (SVG)
# ---------------------------------------------------------------------------

_SPIN_R = 80
_SPIN_CX = 100
_SPIN_CY = 110
_SPIN_COLOURS = {
    "red": "#ef4444",
    "blue": "#3b82f6",
    "green": "#10b981",
    "yellow": "#f59e0b",
    "purple": "#7c3aed",
    "orange": "#f97316",
}


def _render_spinner(spec: dict, params: dict[str, Any]) -> str:
    """Render an SVG spinner/wheel."""
    sectors_ref = spec.get("sectors_from", "")
    sectors = _resolve_or_literal(sectors_ref, params)

    if not isinstance(sectors, list) or not sectors:
        return '<p class="text-realm-purple-300">Spinner data unavailable.</p>'

    n = len(sectors)
    sweep = 360 / n

    lines = []
    lines.append('<div class="my-4 flex justify-center">')
    lines.append(f'<svg viewBox="0 0 200 230" class="w-full max-w-[200px]" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="200" height="230" fill="#3b0f7a" rx="8"/>')
    lines.append(f'  <text x="100" y="18" text-anchor="middle" fill="#f6b935" font-size="12" font-weight="bold">Spinner</text>')

    angle = -90
    for i, colour_name in enumerate(sectors):
        colour = _SPIN_COLOURS.get(colour_name, "#6d28d9")
        start_rad = math.radians(angle)
        end_rad = math.radians(angle + sweep)

        x1 = _SPIN_CX + _SPIN_R * math.cos(start_rad)
        y1 = _SPIN_CY + _SPIN_R * math.sin(start_rad)
        x2 = _SPIN_CX + _SPIN_R * math.cos(end_rad)
        y2 = _SPIN_CY + _SPIN_R * math.sin(end_rad)

        large_arc = 1 if sweep > 180 else 0
        path = (
            f"M {_SPIN_CX},{_SPIN_CY} "
            f"L {x1},{y1} "
            f"A {_SPIN_R},{_SPIN_R} 0 {large_arc} 1 {x2},{y2} Z"
        )
        lines.append(f'  <path d="{path}" fill="{colour}" stroke="#3b0f7a" stroke-width="1.5"/>')

        # Label in sector
        mid_rad = math.radians(angle + sweep / 2)
        tx = _SPIN_CX + _SPIN_R * 0.6 * math.cos(mid_rad)
        ty = _SPIN_CY + _SPIN_R * 0.6 * math.sin(mid_rad)
        lines.append(f'  <text x="{tx}" y="{ty}" text-anchor="middle" fill="white" font-size="9" font-weight="bold">{colour_name}</text>')

        angle += sweep

    # Center circle
    lines.append(f'  <circle cx="{_SPIN_CX}" cy="{_SPIN_CY}" r="8" fill="#1e1b4b" stroke="#f6b935" stroke-width="2"/>')

    # Arrow pointer
    lines.append(f'  <polygon points="{_SPIN_CX},{_SPIN_CY - _SPIN_R - 8} {_SPIN_CX - 6},{_SPIN_CY - _SPIN_R + 4} {_SPIN_CX + 6},{_SPIN_CY - _SPIN_R + 4}" fill="#f6b935"/>')

    # Legend
    unique_colours = list(dict.fromkeys(sectors))
    for i, cn in enumerate(unique_colours):
        col = _SPIN_COLOURS.get(cn, "#6d28d9")
        count = sectors.count(cn)
        ly = _SPIN_CY + _SPIN_R + 18 + i * 15
        lines.append(f'  <rect x="30" y="{ly}" width="10" height="10" fill="{col}" rx="2"/>')
        lines.append(f'  <text x="44" y="{ly + 9}" fill="#d4c4ff" font-size="10">{cn} ({count})</text>')

    lines.append('</svg>')
    lines.append('</div>')

    return "\n".join(lines)


# ===================================================================
# Geography asset renderers
# ===================================================================


# ---------------------------------------------------------------------------
# Matching cards (for grid_fill templates)
# ---------------------------------------------------------------------------

def _render_matching_cards(spec: dict, params: dict[str, Any]) -> str:
    """Render a two-column matching layout.

    The left items are displayed in order; the right column is shuffled.
    The actual matching UI is handled by the quest_question template.
    """
    pairs_ref = spec.get("pairs_from", "")
    data = _resolve_or_literal(pairs_ref, params)

    left_label = spec.get("left_label", "Item")
    right_label = spec.get("right_label", "Match")

    left = data.get("left", []) if isinstance(data, dict) else []
    right = data.get("right", []) if isinstance(data, dict) else []

    if not left or not right:
        return '<p class="text-realm-purple-300">Matching data unavailable.</p>'

    lines = ['<div class="my-4">']
    lines.append(f'  <div class="grid grid-cols-2 gap-4 text-sm">')
    lines.append(f'    <div class="font-bold text-realm-gold-400 pb-2 border-b border-realm-purple-600">{left_label}</div>')
    lines.append(f'    <div class="font-bold text-realm-gold-400 pb-2 border-b border-realm-purple-600">{right_label}</div>')

    for i, item in enumerate(left):
        bg = "bg-realm-purple-800/40" if i % 2 == 0 else "bg-realm-purple-800/20"
        lines.append(f'    <div class="p-2 rounded {bg} text-white">{item}</div>')
        lines.append(f'    <div class="p-2 rounded {bg} text-realm-purple-300">?</div>')

    lines.append('  </div>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Map grid (SVG grid with labeled points)
# ---------------------------------------------------------------------------

def _render_map_grid(spec: dict, params: dict[str, Any]) -> str:
    """Render an SVG grid map with labeled feature points."""
    map_ref = spec.get("map_from", "map")
    data = _resolve_or_literal(map_ref, params)

    if not isinstance(data, dict):
        return '<p class="text-realm-purple-300">Map data unavailable.</p>'

    grid_size = data.get("grid_size", 8)
    features = data.get("features", [])
    east_offset = data.get("east_offset", 10)
    north_offset = data.get("north_offset", 10)
    show_tenths = spec.get("show_tenths", False)

    # Layout constants
    pad_l, pad_b, pad_t, pad_r = 40, 40, 20, 20
    cell = 40  # pixels per grid square
    w = pad_l + grid_size * cell + pad_r
    h = pad_t + grid_size * cell + pad_b

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {w} {h}" class="w-full max-w-md" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{w}" height="{h}" fill="#2d1b5e" rx="8"/>')

    # Grid lines + labels
    for i in range(grid_size + 1):
        x = pad_l + i * cell
        y_top = pad_t
        y_bot = pad_t + grid_size * cell
        # Vertical grid line
        stroke = "#6d28d9" if not show_tenths else "#4c1d95"
        lines.append(f'  <line x1="{x}" y1="{y_top}" x2="{x}" y2="{y_bot}" stroke="{stroke}" stroke-width="0.8"/>')
        # Easting label
        label = east_offset + i
        lines.append(f'  <text x="{x}" y="{y_bot + 15}" text-anchor="middle" fill="#b89aff" font-size="9">{label:02d}</text>')

        y = pad_t + grid_size * cell - i * cell
        x_left = pad_l
        x_right = pad_l + grid_size * cell
        # Horizontal grid line
        lines.append(f'  <line x1="{x_left}" y1="{y}" x2="{x_right}" y2="{y}" stroke="{stroke}" stroke-width="0.8"/>')
        # Northing label
        n_label = north_offset + i
        lines.append(f'  <text x="{x_left - 5}" y="{y + 3}" text-anchor="end" fill="#b89aff" font-size="9">{n_label:02d}</text>')

    # Tenth grid lines (for 6-fig)
    if show_tenths:
        for i in range(grid_size):
            for t in range(1, 10):
                x = pad_l + i * cell + t * cell / 10
                lines.append(f'  <line x1="{x}" y1="{pad_t}" x2="{x}" y2="{pad_t + grid_size * cell}" stroke="#3b1d6e" stroke-width="0.3"/>')
                y = pad_t + grid_size * cell - (i * cell + t * cell / 10)
                lines.append(f'  <line x1="{pad_l}" y1="{y}" x2="{pad_l + grid_size * cell}" y2="{y}" stroke="#3b1d6e" stroke-width="0.3"/>')

    # Feature points
    _POINT_COLOURS = ["#34d399", "#f59e0b", "#ef4444", "#3b82f6", "#ec4899", "#14b8a6"]
    for i, feat in enumerate(features):
        fx = pad_l + feat["x"] * cell
        fy = pad_t + grid_size * cell - feat["y"] * cell
        colour = _POINT_COLOURS[i % len(_POINT_COLOURS)]
        lines.append(f'  <circle cx="{fx}" cy="{fy}" r="5" fill="{colour}" stroke="white" stroke-width="1.5"/>')
        lines.append(f'  <text x="{fx + 8}" y="{fy - 6}" fill="white" font-size="9" font-weight="bold">{feat["name"]}</text>')

    # Axis labels
    lines.append(f'  <text x="{w / 2}" y="{h - 3}" text-anchor="middle" fill="#b89aff" font-size="9">Eastings →</text>')
    lines.append(f'  <text x="8" y="{h / 2}" text-anchor="middle" fill="#b89aff" font-size="9" transform="rotate(-90, 8, {h / 2})">Northings →</text>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Compass rose
# ---------------------------------------------------------------------------

def _render_compass_rose(spec: dict, params: dict[str, Any]) -> str:
    """Render an 8-point compass rose SVG."""
    show_degrees = spec.get("show_degrees", False)

    size = 120
    cx, cy = size // 2, size // 2
    r = 45

    dirs_8 = [
        ("N", 0), ("NE", 45), ("E", 90), ("SE", 135),
        ("S", 180), ("SW", 225), ("W", 270), ("NW", 315),
    ]

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {size} {size}" class="w-24" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{size}" height="{size}" fill="#2d1b5e" rx="8"/>')
    lines.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#6d28d9" stroke-width="1"/>')

    for label, deg in dirs_8:
        rad = math.radians(deg - 90)  # -90 to put N at top
        tx = cx + r * 1.15 * math.cos(rad)
        ty = cy + r * 1.15 * math.sin(rad)
        # Tick mark
        ix = cx + (r - 4) * math.cos(rad)
        iy = cy + (r - 4) * math.sin(rad)
        ox = cx + (r + 2) * math.cos(rad)
        oy = cy + (r + 2) * math.sin(rad)
        lines.append(f'  <line x1="{ix}" y1="{iy}" x2="{ox}" y2="{oy}" stroke="#f6b935" stroke-width="1.5"/>')

        font_size = "10" if len(label) <= 2 else "8"
        colour = "#f6b935" if label == "N" else "#d4c4ff"
        lines.append(f'  <text x="{tx}" y="{ty + 3}" text-anchor="middle" fill="{colour}" font-size="{font_size}" font-weight="bold">{label}</text>')

        if show_degrees and deg > 0:
            dx = cx + (r * 0.7) * math.cos(rad)
            dy = cy + (r * 0.7) * math.sin(rad)
            lines.append(f'  <text x="{dx}" y="{dy + 3}" text-anchor="middle" fill="#8b6fc0" font-size="7">{deg:03d}°</text>')

    # Arrow pointing north
    lines.append(f'  <polygon points="{cx},{cy - r + 10} {cx - 4},{cy} {cx + 4},{cy}" fill="#f6b935"/>')
    lines.append(f'  <polygon points="{cx},{cy + r - 10} {cx - 4},{cy} {cx + 4},{cy}" fill="#6d28d9"/>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scale bar
# ---------------------------------------------------------------------------

def _render_scale_bar(spec: dict, params: dict[str, Any]) -> str:
    """Render a simple scale bar SVG."""
    ratio_ref = spec.get("ratio_from", "")
    ratio = _resolve_or_literal(ratio_ref, params)
    if not isinstance(ratio, (int, float)):
        ratio = 50000

    # Calculate what 1 cm on map = in real life
    real_m_per_cm = ratio / 100  # ratio is cm:cm, so 1cm map = ratio cm real = ratio/100 m
    real_km_per_cm = real_m_per_cm / 1000

    w, h = 260, 60
    bar_y = 30
    segments = 4
    seg_w = 40  # pixels per segment

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {w} {h}" class="w-full max-w-xs" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{w}" height="{h}" fill="#2d1b5e" rx="6"/>')

    x_start = 30
    for i in range(segments):
        x = x_start + i * seg_w
        fill = "#f6b935" if i % 2 == 0 else "#6d28d9"
        lines.append(f'  <rect x="{x}" y="{bar_y}" width="{seg_w}" height="10" fill="{fill}" stroke="white" stroke-width="0.5"/>')

    # Labels
    for i in range(segments + 1):
        x = x_start + i * seg_w
        km_val = real_km_per_cm * i
        lines.append(f'  <text x="{x}" y="{bar_y - 5}" text-anchor="middle" fill="#d4c4ff" font-size="8">{km_val:.1f} km</text>')

    lines.append(f'  <text x="{w / 2}" y="{h - 5}" text-anchor="middle" fill="#b89aff" font-size="8">Scale 1 : {ratio:,}</text>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Climograph (dual-axis: temp line + rainfall bars)
# ---------------------------------------------------------------------------

def _render_climograph(spec: dict, params: dict[str, Any]) -> str:
    """Render a climate graph with temperature line and rainfall bars."""
    climate_ref = spec.get("climate_from", "climate")
    data = _resolve_or_literal(climate_ref, params)
    title = spec.get("title", "")

    if not isinstance(data, dict):
        return '<p class="text-realm-purple-300">Climate data unavailable.</p>'

    months = data.get("months", [])
    temp_c = data.get("temp_c", [])
    rain_mm = data.get("rain_mm", [])

    if not months or not temp_c or not rain_mm:
        return '<p class="text-realm-purple-300">Climate data incomplete.</p>'

    n = 12
    w, h = 400, 280
    pad_l, pad_r, pad_t, pad_b = 55, 50, 30, 40
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    t_min = min(temp_c[:n])
    t_max = max(temp_c[:n])
    t_range = t_max - t_min or 1
    r_max = max(rain_mm[:n]) or 1

    bar_w = plot_w / n * 0.6

    def px(i: int) -> float:
        return pad_l + (i + 0.5) / n * plot_w

    def py_temp(t: float) -> float:
        return pad_t + plot_h - ((t - t_min) / t_range) * plot_h

    def py_rain(r: float) -> float:
        return pad_t + plot_h - (r / r_max) * plot_h

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {w} {h}" class="w-full max-w-md" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{w}" height="{h}" fill="#2d1b5e" rx="8"/>')

    if title:
        lines.append(f'  <text x="{w / 2}" y="18" text-anchor="middle" fill="#f6b935" font-size="12" font-weight="bold">{title}</text>')

    # Y-axis labels — temperature (left)
    for i in range(6):
        t = t_min + (t_range * i / 5)
        y = py_temp(t)
        lines.append(f'  <line x1="{pad_l}" y1="{y}" x2="{w - pad_r}" y2="{y}" stroke="#4c1d95" stroke-width="0.3"/>')
        lines.append(f'  <text x="{pad_l - 5}" y="{y + 3}" text-anchor="end" fill="#ef4444" font-size="8">{t:.0f}°C</text>')

    # Y-axis labels — rainfall (right)
    for i in range(6):
        r = r_max * i / 5
        y = py_rain(r)
        lines.append(f'  <text x="{w - pad_r + 5}" y="{y + 3}" text-anchor="start" fill="#3b82f6" font-size="8">{r:.0f}</text>')

    lines.append(f'  <text x="{w - 15}" y="{pad_t - 5}" text-anchor="end" fill="#3b82f6" font-size="8">mm</text>')

    # Rainfall bars
    for i in range(n):
        x = px(i) - bar_w / 2
        y = py_rain(rain_mm[i])
        bar_h_px = pad_t + plot_h - y
        lines.append(f'  <rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h_px}" fill="#3b82f6" opacity="0.6" rx="1"/>')

    # Temperature line
    temp_pts = " ".join(f"{px(i)},{py_temp(temp_c[i])}" for i in range(n))
    lines.append(f'  <polyline points="{temp_pts}" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for i in range(n):
        lines.append(f'  <circle cx="{px(i)}" cy="{py_temp(temp_c[i])}" r="3" fill="#ef4444" stroke="white" stroke-width="1"/>')

    # Month labels
    for i in range(n):
        lines.append(f'  <text x="{px(i)}" y="{h - 10}" text-anchor="middle" fill="#d4c4ff" font-size="9">{months[i]}</text>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Contour map (SVG)
# ---------------------------------------------------------------------------

def _render_contours(spec: dict, params: dict[str, Any]) -> str:
    """Render a contour map with elliptical contour lines."""
    contour_ref = spec.get("contour_data_from", "contour_map")
    data = _resolve_or_literal(contour_ref, params)

    if not isinstance(data, dict):
        return '<p class="text-realm-purple-300">Contour data unavailable.</p>'

    contours = data.get("contours", [])
    marked = data.get("marked_point", {})
    interval = data.get("interval", 20)
    mw = data.get("map_width", 300)
    mh = data.get("map_height", 260)
    line_ab = data.get("line_ab")

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {mw} {mh}" class="w-full max-w-sm" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{mw}" height="{mh}" fill="#2d1b5e" rx="8"/>')

    # Contour lines (outer to inner)
    for c in contours:
        lines.append(
            f'  <ellipse cx="{c["cx"]}" cy="{c["cy"]}" rx="{c["rx"]}" ry="{c["ry"]}" '
            f'fill="none" stroke="#8b6fc0" stroke-width="1"/>'
        )
        # Label every other contour
        if c["height"] % (interval * 2) == 0:
            lx = c["cx"] + c["rx"] + 3
            lines.append(f'  <text x="{lx}" y="{c["cy"] + 3}" fill="#d4c4ff" font-size="8">{c["height"]}m</text>')

    # Marked point P
    if marked:
        lines.append(f'  <circle cx="{marked["x"]}" cy="{marked["y"]}" r="4" fill="#ef4444" stroke="white" stroke-width="1.5"/>')
        lines.append(f'  <text x="{marked["x"] + 7}" y="{marked["y"] - 5}" fill="#ef4444" font-size="10" font-weight="bold">P</text>')

    # Line A—B for cross-section
    if line_ab:
        lines.append(
            f'  <line x1="{line_ab["ax"]}" y1="{line_ab["ay"]}" '
            f'x2="{line_ab["bx"]}" y2="{line_ab["by"]}" '
            f'stroke="#f6b935" stroke-width="1.5" stroke-dasharray="4,3"/>'
        )
        lines.append(f'  <text x="{line_ab["ax"] - 8}" y="{line_ab["ay"] + 4}" fill="#f6b935" font-size="10" font-weight="bold">A</text>')
        lines.append(f'  <text x="{line_ab["bx"] + 4}" y="{line_ab["by"] + 4}" fill="#f6b935" font-size="10" font-weight="bold">B</text>')

    # Interval label
    lines.append(f'  <text x="10" y="{mh - 8}" fill="#b89aff" font-size="8">Contour interval: {interval}m</text>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-section set (SVG)
# ---------------------------------------------------------------------------

def _render_cross_section_set(spec: dict, params: dict[str, Any]) -> str:
    """Render a set of cross-section profile options."""
    contour_ref = spec.get("contour_data_from", "contour_map")
    data = _resolve_or_literal(contour_ref, params)

    if not isinstance(data, dict) or "cross_sections" not in data:
        return '<p class="text-realm-purple-300">Cross-section data unavailable.</p>'

    cs = data["cross_sections"]
    options = cs.get("options", [])
    labels = cs.get("labels", [])
    peak = data.get("peak", 200)

    pw, ph = 200, 60  # per-profile dimensions

    lines = ['<div class="my-4 grid grid-cols-2 gap-2">']

    for profile, label in zip(options, labels):
        lines.append('<div class="text-center">')
        lines.append(f'<svg viewBox="0 0 {pw} {ph}" class="w-full" xmlns="http://www.w3.org/2000/svg">')
        lines.append(f'  <rect width="{pw}" height="{ph}" fill="#2d1b5e" rx="4"/>')

        # Draw profile
        n = len(profile)
        pts = []
        for i, h_val in enumerate(profile):
            x = 10 + (i / max(n - 1, 1)) * (pw - 20)
            y = ph - 10 - (h_val / max(peak, 1)) * (ph - 20)
            pts.append(f"{x},{y}")

        # Close polygon for fill
        poly = " ".join(pts) + f" {pw - 10},{ph - 10} 10,{ph - 10}"
        lines.append(f'  <polygon points="{poly}" fill="#8b6fc0" opacity="0.4"/>')
        pts_str = " ".join(pts)
        lines.append(f'  <polyline points="{pts_str}" fill="none" stroke="#d4c4ff" stroke-width="1.5"/>')
        lines.append(f'  <text x="{pw / 2}" y="{ph - 2}" text-anchor="middle" fill="#f6b935" font-size="9" font-weight="bold">Profile {label}</text>')

        lines.append('</svg>')
        lines.append('</div>')

    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Synoptic chart (simplified isobars with H/L)
# ---------------------------------------------------------------------------

def _render_synoptic_chart(spec: dict, params: dict[str, Any]) -> str:
    """Render a simplified synoptic chart with pressure centers."""
    chart_ref = spec.get("chart_from", "chart")
    data = _resolve_or_literal(chart_ref, params)

    if not isinstance(data, dict):
        return '<p class="text-realm-purple-300">Synoptic chart unavailable.</p>'

    centers = data.get("centers", [])
    w, h = 300, 260

    # Map regions to approximate positions
    region_pos = {
        "North-west": (80, 80),
        "North-east": (220, 80),
        "South-west": (80, 180),
        "South-east": (220, 180),
    }

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {w} {h}" class="w-full max-w-sm" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{w}" height="{h}" fill="#2d1b5e" rx="8"/>')
    lines.append(f'  <text x="{w / 2}" y="18" text-anchor="middle" fill="#f6b935" font-size="11" font-weight="bold">Pressure Map</text>')

    for center in centers:
        pos = region_pos.get(center["region"], (150, 130))
        rcx, rcy = pos
        hl = center["type"]
        pressure = center["pressure"]
        tight = center.get("tight", False)

        # Concentric isobars
        for i in range(3):
            ir = 55 - i * 15 if tight else 60 - i * 18
            ir = max(ir, 10)
            sw = "1.5" if tight else "0.8"
            lines.append(f'  <ellipse cx="{rcx}" cy="{rcy}" rx="{ir}" ry="{ir * 0.8}" fill="none" stroke="#8b6fc0" stroke-width="{sw}"/>')

        # H/L label
        colour = "#ef4444" if hl == "L" else "#3b82f6"
        lines.append(f'  <text x="{rcx}" y="{rcy + 5}" text-anchor="middle" fill="{colour}" font-size="18" font-weight="bold">{hl}</text>')
        lines.append(f'  <text x="{rcx}" y="{rcy + 18}" text-anchor="middle" fill="#d4c4ff" font-size="8">{pressure} mb</text>')

    # Region labels
    for region, (rx, ry) in region_pos.items():
        lines.append(f'  <text x="{rx}" y="{ry - 55}" text-anchor="middle" fill="#b89aff" font-size="7">{region}</text>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rainfall diagram
# ---------------------------------------------------------------------------

def _render_rainfall_diagram(spec: dict, params: dict[str, Any]) -> str:
    """Render a simple rainfall type diagram."""
    rainfall_ref = spec.get("rainfall_from", "rainfall")
    data = _resolve_or_literal(rainfall_ref, params)

    if not isinstance(data, dict):
        return '<p class="text-realm-purple-300">Rainfall data unavailable.</p>'

    rainfall_type = data.get("type", "relief")
    w, h = 320, 200

    lines = ['<div class="my-4 flex justify-center">']
    lines.append(f'<svg viewBox="0 0 {w} {h}" class="w-full max-w-sm" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'  <rect width="{w}" height="{h}" fill="#2d1b5e" rx="8"/>')
    # Arrow marker definition
    lines.append('  <defs><marker id="arr" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto"><path d="M0,0 L6,2 L0,4" fill="#34d399"/></marker></defs>')

    if rainfall_type == "relief":
        # Mountain shape
        lines.append('  <polygon points="60,170 160,60 260,170" fill="#6d28d9" stroke="#8b6fc0" stroke-width="1"/>')
        # Wind arrows from left
        for y in [90, 110, 130]:
            lines.append(f'  <line x1="10" y1="{y}" x2="50" y2="{y}" stroke="#34d399" stroke-width="1.5" marker-end="url(#arr)"/>')
        # Rising air
        lines.append('  <line x1="110" y1="130" x2="110" y2="70" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4,3"/>')
        # Cloud and rain
        lines.append('  <ellipse cx="100" cy="55" rx="30" ry="12" fill="#94a3b8" opacity="0.7"/>')
        for dx in [-10, 0, 10]:
            lines.append(f'  <line x1="{100 + dx}" y1="67" x2="{100 + dx - 3}" y2="85" stroke="#3b82f6" stroke-width="1.5"/>')
        lines.append('  <text x="230" y="100" text-anchor="middle" fill="#d4c4ff" font-size="9">Dry side</text>')
        lines.append('  <text x="60" y="45" text-anchor="middle" fill="#d4c4ff" font-size="9">Wet side</text>')

    elif rainfall_type == "convectional":
        # Ground
        lines.append('  <rect x="40" y="160" width="240" height="20" fill="#b45309" rx="2"/>')
        # Sun
        lines.append('  <circle cx="160" cy="30" r="15" fill="#f59e0b"/>')
        for dx in [-30, 0, 30]:
            lines.append(f'  <line x1="{160 + dx}" y1="50" x2="{160 + dx}" y2="145" stroke="#f59e0b" stroke-width="1" stroke-dasharray="3,3"/>')
        # Rising air
        lines.append('  <line x1="160" y1="140" x2="160" y2="75" stroke="#34d399" stroke-width="2" stroke-dasharray="5,3"/>')
        lines.append('  <polygon points="160,70 155,80 165,80" fill="#34d399"/>')
        # Cloud + rain
        lines.append('  <ellipse cx="160" cy="65" rx="40" ry="15" fill="#94a3b8" opacity="0.7"/>')
        for dx in [-15, 0, 15]:
            lines.append(f'  <line x1="{160 + dx}" y1="80" x2="{160 + dx - 3}" y2="100" stroke="#3b82f6" stroke-width="1.5"/>')

    elif rainfall_type == "frontal":
        # Cold air mass
        lines.append('  <polygon points="20,170 20,90 120,90 120,170" fill="#3b82f6" opacity="0.3"/>')
        lines.append('  <text x="70" y="140" text-anchor="middle" fill="#93c5fd" font-size="9">Cold air</text>')
        # Warm air mass
        lines.append('  <polygon points="120,170 120,90 200,50 260,50 260,170" fill="#ef4444" opacity="0.2"/>')
        lines.append('  <text x="220" y="100" text-anchor="middle" fill="#fca5a5" font-size="9">Warm air</text>')
        # Front line
        lines.append('  <line x1="120" y1="170" x2="200" y2="50" stroke="#f6b935" stroke-width="2"/>')
        # Cloud + rain
        lines.append('  <ellipse cx="170" cy="55" rx="35" ry="12" fill="#94a3b8" opacity="0.7"/>')
        for dx in [-10, 5, 20]:
            lines.append(f'  <line x1="{170 + dx}" y1="67" x2="{170 + dx - 3}" y2="90" stroke="#3b82f6" stroke-width="1.5"/>')
        lines.append('  <line x1="150" y1="120" x2="170" y2="70" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4,3"/>')

    lines.append('</svg>')
    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Map image renderer
# ---------------------------------------------------------------------------

def _render_map_image(spec: dict, params: dict[str, Any]) -> str:
    """Render an <img> tag pointing to a static map image."""
    src = spec.get("src", "")
    alt = spec.get("alt", "Map")
    caption = spec.get("caption", "")

    lines = [
        '<div class="my-4 text-center">',
        f'  <img src="{src}" alt="{alt}" '
        'class="mx-auto rounded-lg border border-realm-purple-500/30 max-w-full" '
        'style="max-height: 500px;" />',
    ]
    if caption:
        lines.append(
            f'  <p class="text-xs text-realm-purple-400 mt-2 italic">{caption}</p>'
        )
    lines.append('</div>')
    return "\n".join(lines)
