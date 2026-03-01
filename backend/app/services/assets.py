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
    title = spec.get("title", "")

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
