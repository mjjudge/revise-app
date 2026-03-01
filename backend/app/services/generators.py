"""Deterministic parameter generators for question templates.

Each generator function takes a Random instance (seeded) and the parameter spec
from the YAML template, and returns the generated value(s).
"""

from __future__ import annotations

import math
import random as _random_mod
from fractions import Fraction
from typing import Any


# ---------------------------------------------------------------------------
# Generator registry
# ---------------------------------------------------------------------------

_GENERATORS: dict[str, Any] = {}


def register_gen(name: str):
    """Decorator to register a parameter generator."""
    def decorator(fn):
        _GENERATORS[name] = fn
        return fn
    return decorator


def generate_param(rng: _random_mod.Random, spec: dict[str, Any], context: dict[str, Any]) -> Any:
    """Dispatch to the right generator based on spec['gen']."""
    gen_name = spec.get("gen")
    if gen_name is None:
        raise ValueError(f"Parameter spec missing 'gen' key: {spec}")
    if gen_name not in _GENERATORS:
        raise ValueError(f"Unknown generator: '{gen_name}'")
    return _GENERATORS[gen_name](rng, spec, context)


# ---------------------------------------------------------------------------
# Integer / decimal generators
# ---------------------------------------------------------------------------

@register_gen("int")
def gen_int(rng: _random_mod.Random, spec: dict, ctx: dict) -> int:
    r = spec.get("range", {})
    lo, hi = r.get("min", 1), r.get("max", 100)
    return rng.randint(lo, hi)


@register_gen("decimal")
def gen_decimal(rng: _random_mod.Random, spec: dict, ctx: dict) -> float:
    r = spec.get("range", {})
    lo, hi = r.get("min", 0.01), r.get("max", 999.99)
    dp = spec.get("dp", 4)
    val = rng.uniform(lo, hi)
    return round(val, dp)


@register_gen("int_or_decimal")
def gen_int_or_decimal(rng: _random_mod.Random, spec: dict, ctx: dict) -> float:
    r = spec.get("range", {})
    lo, hi = r.get("min", 1), r.get("max", 100)
    decimals = spec.get("decimals", {})
    allowed = decimals.get("allowed", [0])
    prefer = decimals.get("prefer", 0)
    # Weighted choice: prefer integer
    dp = rng.choices(allowed, weights=[3 if d == prefer else 1 for d in allowed], k=1)[0]
    if dp == 0:
        return float(rng.randint(int(lo), int(hi)))
    val = rng.uniform(lo, hi)
    return round(val, dp)


# ---------------------------------------------------------------------------
# List generators
# ---------------------------------------------------------------------------

@register_gen("int_list")
def gen_int_list(rng: _random_mod.Random, spec: dict, ctx: dict) -> list[int]:
    count_spec = spec.get("count", {})
    count = rng.randint(count_spec.get("min", 5), count_spec.get("max", 10))
    r = spec.get("range", {})
    lo, hi = r.get("min", 1), r.get("max", 30)
    ensure = spec.get("ensure", {})

    if ensure.get("odd_count"):
        if count % 2 == 0:
            count += 1

    if ensure.get("divisible_mean"):
        # Generate values such that their sum is divisible by count
        values = [rng.randint(lo, hi) for _ in range(count)]
        remainder = sum(values) % count
        if remainder != 0:
            # Adjust last value to make sum divisible
            adjustment = count - remainder
            if values[-1] + adjustment <= hi:
                values[-1] += adjustment
            else:
                values[-1] -= remainder
                if values[-1] < lo:
                    values[-1] = lo
                    # Adjust another value
                    remainder = sum(values) % count
                    if remainder != 0:
                        values[0] += (count - remainder)
        return values

    return [rng.randint(lo, hi) for _ in range(count)]


@register_gen("int_list_with_mode")
def gen_int_list_with_mode(rng: _random_mod.Random, spec: dict, ctx: dict) -> list[int]:
    count_spec = spec.get("count", {})
    count = rng.randint(count_spec.get("min", 7), count_spec.get("max", 10))
    r = spec.get("range", {})
    lo, hi = r.get("min", 1), r.get("max", 15)

    # Pick a mode value and ensure it appears more than any other
    mode_val = rng.randint(lo, hi)
    mode_count = rng.randint(3, min(count - 2, 4))
    values = [mode_val] * mode_count

    # Fill remaining with non-repeating-enough values
    remaining = count - mode_count
    others = []
    for _ in range(remaining):
        v = rng.randint(lo, hi)
        while v == mode_val or others.count(v) >= mode_count - 1:
            v = rng.randint(lo, hi)
        others.append(v)
    values.extend(others)
    rng.shuffle(values)
    return values


# ---------------------------------------------------------------------------
# Pick one from a list
# ---------------------------------------------------------------------------

@register_gen("pick_one")
def gen_pick_one(rng: _random_mod.Random, spec: dict, ctx: dict) -> Any:
    options = spec.get("from", [])
    if isinstance(options, list):
        return rng.choice(options)
    # Might be a context reference like "categories.labels"
    ref = options
    parts = ref.split(".")
    val = ctx
    for p in parts:
        val = val[p] if isinstance(val, dict) else getattr(val, p)
    return rng.choice(val)


# ---------------------------------------------------------------------------
# Categorical data (for pie charts / tables)
# ---------------------------------------------------------------------------

@register_gen("categorical_counts")
def gen_categorical_counts(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    labels = spec.get("labels", ["A", "B", "C", "D"])
    cr = spec.get("count_range", {})
    lo, hi = cr.get("min", 2), cr.get("max", 20)
    ensure = spec.get("ensure", {})
    total_min = ensure.get("total_min", 10)

    counts = [rng.randint(lo, hi) for _ in labels]
    # Ensure minimum total
    while sum(counts) < total_min:
        idx = rng.randint(0, len(counts) - 1)
        counts[idx] += 1

    return {"labels": labels, "counts": counts, "total": sum(counts)}


# ---------------------------------------------------------------------------
# Context-aware dataset scenarios (for line graphs)
# ---------------------------------------------------------------------------

# Each scenario bundles a context label, sensible y-range, unit, and chart title.
# Ranges are realistic for UK KS3 students.
_LINE_GRAPH_SCENARIOS_WEEKLY = [
    {"context": "daily step count",       "y_min": 2000, "y_max": 12000, "unit": "steps",    "title": "Steps per day"},
    {"context": "number of visitors",     "y_min": 15,   "y_max": 90,    "unit": "",          "title": "Visitors per day"},
    {"context": "temperature at noon",    "y_min": 5,    "y_max": 25,    "unit": "°C",        "title": "Noon temperature (°C)"},
    {"context": "hours of sunshine",      "y_min": 0,    "y_max": 14,    "unit": "hours",     "title": "Hours of sunshine"},
    {"context": "books borrowed",         "y_min": 3,    "y_max": 30,    "unit": "",          "title": "Books borrowed per day"},
    {"context": "glasses of water drunk", "y_min": 2,    "y_max": 10,    "unit": "glasses",   "title": "Glasses of water per day"},
]

_LINE_GRAPH_SCENARIOS_MONTHLY = [
    {"context": "monthly rainfall",       "y_min": 20,   "y_max": 120,   "unit": "mm",        "title": "Rainfall (mm)"},
    {"context": "ice cream sales",        "y_min": 50,   "y_max": 500,   "unit": "£",         "title": "Ice cream sales (£)"},
    {"context": "library visitors",       "y_min": 80,   "y_max": 350,   "unit": "",          "title": "Library visitors per month"},
    {"context": "average temperature",    "y_min": 2,    "y_max": 22,    "unit": "°C",        "title": "Average temperature (°C)"},
    {"context": "electricity usage",      "y_min": 150,  "y_max": 500,   "unit": "kWh",       "title": "Electricity usage (kWh)"},
    {"context": "park visitors",          "y_min": 100,  "y_max": 800,   "unit": "",          "title": "Park visitors per month"},
]


@register_gen("context_dataset")
def gen_context_dataset(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    """Pick a context-appropriate scenario with sensible data ranges.

    The result dict contains: context, y_min, y_max, unit, title.
    These values are placed into ctx so that downstream generators
    (time_series, line_graph_statements) can use them.
    """
    period = spec.get("period", "weekly")
    scenarios = _LINE_GRAPH_SCENARIOS_WEEKLY if period == "weekly" else _LINE_GRAPH_SCENARIOS_MONTHLY
    chosen = rng.choice(scenarios)
    return dict(chosen)


# ---------------------------------------------------------------------------
# Time series (for line graphs)
# ---------------------------------------------------------------------------

@register_gen("time_series")
def gen_time_series(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    n = spec.get("points", 6)
    x_labels = spec.get("x_labels", [f"T{i}" for i in range(n)])

    # y_range can come from spec directly or from a context_dataset in ctx
    yr = spec.get("y_range", {})
    ctx_scenario = ctx.get(spec.get("scenario_from", ""), {})
    lo = yr.get("min") or ctx_scenario.get("y_min", 10)
    hi = yr.get("max") or ctx_scenario.get("y_max", 60)

    pattern = spec.get("pattern", {}).get("type", "random")

    if pattern == "single_peak":
        peak_idx = rng.randint(1, n - 2)
        peak_val = rng.randint(int(hi * 0.7), hi)
        base = rng.randint(lo, int(hi * 0.4))
        y = []
        for i in range(n):
            dist = abs(i - peak_idx)
            val = peak_val - dist * rng.randint(3, 8)
            y.append(max(lo, min(hi, val)))
    else:
        y = [rng.randint(lo, hi) for _ in range(n)]

    return {"x": x_labels[:n], "y": y}


@register_gen("line_graph_statements")
def gen_line_graph_statements(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    """Generate true + distractor statements about a time series dataset."""
    ref = spec.get("from", "dataset")
    dataset = ctx.get(ref, {})
    x = dataset.get("x", [])
    y = dataset.get("y", [])

    if not y:
        return {"correct": "The data increases overall.", "distractors": ["No data."]}

    max_idx = y.index(max(y))
    min_idx = y.index(min(y))

    correct = f"The highest value is on {x[max_idx]}."
    distractors = [
        f"The lowest value is on {x[max_idx]}.",  # deliberately wrong
        f"The value on {x[0]} is {y[0] + rng.randint(5, 15)}.",
        f"The data stays the same throughout.",
    ]
    count = spec.get("count", 3)
    rng.shuffle(distractors)
    return {"correct": correct, "distractors": distractors[:count]}


# ---------------------------------------------------------------------------
# Algebra generators
# ---------------------------------------------------------------------------

@register_gen("linear_expression")
def gen_linear_expression(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    variables = spec.get("vars", ["x"])
    cr = spec.get("coeff_range", {})
    clo, chi = cr.get("min", -5), cr.get("max", 8)
    const_r = spec.get("const_range", {})
    klo, khi = const_r.get("min", -10), const_r.get("max", 10)

    coeffs = {}
    terms = []
    for var in variables:
        c = rng.randint(clo, chi)
        while c == 0:
            c = rng.randint(clo, chi)
        coeffs[var] = c
        if c == 1:
            terms.append(var)
        elif c == -1:
            terms.append(f"-{var}")
        else:
            terms.append(f"{c}{var}")

    const = rng.randint(klo, khi)
    if const != 0:
        terms.append(str(const))

    expr_str = terms[0]
    for t in terms[1:]:
        if t.startswith("-"):
            expr_str += f" - {t[1:]}"
        else:
            expr_str += f" + {t}"

    return {"expr_str": expr_str, "coeffs": coeffs, "const": const, "vars": variables}


@register_gen("var_assignments")
def gen_var_assignments(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    # Get vars from the expression context
    vars_from = spec.get("vars_from", "expr.vars")
    parts = vars_from.split(".")
    val = ctx
    for p in parts:
        val = val[p] if isinstance(val, dict) else getattr(val, p)
    variables = val

    vr = spec.get("value_range", {})
    lo, hi = vr.get("min", -6), vr.get("max", 9)

    assignments = {}
    for var in variables:
        assignments[var] = rng.randint(lo, hi)

    # Format as string: "x = 3 and y = -2"
    parts_str = [f"{v} = {assignments[v]}" for v in variables]
    assignments["text"] = " and ".join(parts_str)
    return assignments


@register_gen("like_terms_expression")
def gen_like_terms_expression(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    var = spec.get("var", "a")
    tc = spec.get("term_count", {})
    n_terms = rng.randint(tc.get("min", 4), tc.get("max", 7))
    cr = spec.get("coeff_range", {})
    clo, chi = cr.get("min", -9), cr.get("max", 9)
    ensure = spec.get("ensure", {})

    coeffs = []
    for _ in range(n_terms):
        c = rng.randint(clo, chi)
        while c == 0:
            c = rng.randint(clo, chi)
        coeffs.append(c)

    if ensure.get("has_both_signs"):
        if all(c > 0 for c in coeffs):
            coeffs[rng.randint(0, len(coeffs) - 1)] = rng.randint(clo, -1)
        elif all(c < 0 for c in coeffs):
            coeffs[rng.randint(0, len(coeffs) - 1)] = rng.randint(1, chi)

    # Build display string
    terms = []
    for c in coeffs:
        if c == 1:
            terms.append(var)
        elif c == -1:
            terms.append(f"-{var}")
        else:
            terms.append(f"{c}{var}")

    expr_str = terms[0]
    for t in terms[1:]:
        if t.startswith("-"):
            expr_str += f" - {t[1:]}"
        else:
            expr_str += f" + {t}"

    total = sum(coeffs)
    return {"expr_str": expr_str, "coeffs": coeffs, "var": var, "total_coeff": total}


# ---------------------------------------------------------------------------
# Metric conversion
# ---------------------------------------------------------------------------

_METRIC_DIMENSIONS = {
    "length": {"mm": 1, "cm": 10, "m": 1000, "km": 1_000_000},
    "mass": {"g": 1, "kg": 1000},
    "volume": {"ml": 1, "l": 1000},
}


@register_gen("metric_conversion")
def gen_metric_conversion(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    # Pick a random dimension, then two different units
    dim_name = rng.choice(list(_METRIC_DIMENSIONS.keys()))
    units = _METRIC_DIMENSIONS[dim_name]
    unit_list = list(units.keys())
    from_unit = rng.choice(unit_list)
    to_unit = rng.choice(unit_list)
    while to_unit == from_unit:
        to_unit = rng.choice(unit_list)

    factor = units[from_unit] / units[to_unit]  # multiply value by this
    return {
        "from_unit": from_unit,
        "to_unit": to_unit,
        "factor": factor,
        "dimension": dim_name,
    }


# ---------------------------------------------------------------------------
# Arithmetic expression (BIDMAS)
# ---------------------------------------------------------------------------

@register_gen("arithmetic_expression")
def gen_arithmetic_expression(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    """Generate a BIDMAS expression with brackets that evaluates to an integer."""
    ensure = spec.get("ensure", {})

    for _ in range(50):  # retry until we get an integer result
        # Pick small integers for operands
        a = rng.randint(2, 9)
        b = rng.randint(2, 6)
        c = rng.randint(1, 8)
        d = rng.randint(2, 5)

        # Pick pattern with brackets
        patterns = [
            (f"({a} + {b}) * {c}", (a + b) * c),
            (f"{a} * ({b} + {c})", a * (b + c)),
            (f"({a} + {b}) * {c} - {d}", (a + b) * c - d),
            (f"{a} + {b} * ({c} - {d})", a + b * (c - d)) if c > d else None,
            (f"({a} + {b}) ** 2", (a + b) ** 2) if a + b <= 12 else None,
            (f"{a} ** 2 + {b} * {c}", a ** 2 + b * c),
            (f"({a} - {b}) * {c} + {d}", (a - b) * c + d) if a > b else None,
        ]
        # Filter out None
        valid = [p for p in patterns if p is not None]
        expr_str, result = rng.choice(valid)

        if isinstance(result, int) or (isinstance(result, float) and result == int(result)):
            # Replace ** N with Unicode superscript for display
            import re
            def _superscript(m):
                _map = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
                        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
                return "".join(_map[ch] for ch in m.group(1))
            display = re.sub(r"\*\*\s*(\d+)", _superscript, expr_str)
            return {"expr_str": display, "result": int(result)}

    # Fallback
    return {"expr_str": f"({2} + {3}) * {4}", "result": 20}


# ---------------------------------------------------------------------------
# Probability generators
# ---------------------------------------------------------------------------

@register_gen("probability_events")
def gen_probability_events(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    """Generate events with known probability ordering."""
    events_pool = [
        ("It will rain chocolate tomorrow", 0.0),
        ("You flip a coin and get heads", 0.5),
        ("The sun will rise tomorrow", 1.0),
        ("You roll a 6 on a fair die", 1 / 6),
        ("You roll an even number on a fair die", 0.5),
        ("A day picked at random is a weekend day", 2 / 7),
        ("You pick a red card from a standard pack", 0.5),
        ("A baby born today is born on a Tuesday", 1 / 7),
        ("It will snow in summer in England", 0.02),
        ("You roll less than 5 on a fair die", 4 / 6),
    ]
    count = spec.get("count", 4)
    chosen = rng.sample(events_pool, min(count, len(events_pool)))
    # Sort by probability for the correct order
    sorted_events = sorted(chosen, key=lambda x: x[1])
    return {
        "events": [e[0] for e in chosen],  # unsorted (display order)
        "correct_order": [e[0] for e in sorted_events],
        "probabilities": {e[0]: e[1] for e in chosen},
    }


@register_gen("equally_likely_scenario")
def gen_equally_likely_scenario(rng: _random_mod.Random, spec: dict, ctx: dict) -> dict:
    types = spec.get("types", ["die", "coin", "spinner"])
    chosen_type = rng.choice(types)

    if chosen_type == "die":
        total = 6
        target = rng.randint(1, 6)
        return {
            "object_name": "die",
            "event_description": f"rolling a {target}",
            "favourable": 1,
            "total": total,
            "probability": Fraction(1, 6),
        }
    elif chosen_type == "coin":
        side = rng.choice(["heads", "tails"])
        return {
            "object_name": "coin",
            "event_description": f"getting {side}",
            "favourable": 1,
            "total": 2,
            "probability": Fraction(1, 2),
        }
    else:  # spinner
        n_sectors = rng.choice([4, 5, 6, 8])
        colours = ["red", "blue", "green", "yellow", "purple", "orange"][:n_sectors]
        target_colour = rng.choice(colours)
        target_count = rng.randint(1, max(1, n_sectors // 2))
        # Build sectors
        sectors = [target_colour] * target_count
        remaining = n_sectors - target_count
        other_colours = [c for c in colours if c != target_colour]
        for i in range(remaining):
            sectors.append(other_colours[i % len(other_colours)])
        rng.shuffle(sectors)
        return {
            "object_name": "spinner",
            "event_description": f"landing on {target_colour}",
            "favourable": target_count,
            "total": n_sectors,
            "probability": Fraction(target_count, n_sectors),
            "sectors": sectors,
        }


@register_gen("from_scenario")
def gen_from_scenario(rng: _random_mod.Random, spec: dict, ctx: dict) -> Any:
    """Extract a field from a previously generated scenario."""
    field = spec.get("field", "")
    scenario = ctx.get("scenario", {})
    return scenario.get(field, "")


@register_gen("probability_fraction")
def gen_probability_fraction(rng: _random_mod.Random, spec: dict, ctx: dict) -> Fraction:
    denom = spec.get("denom", 10)
    ensure = spec.get("ensure", {})
    lo = ensure.get("min", 1)
    hi = ensure.get("max", denom - 1)
    num = rng.randint(lo, hi)
    return Fraction(num, denom)


@register_gen("int_dependent")
def gen_int_dependent(rng: _random_mod.Random, spec: dict, ctx: dict) -> int:
    """Generate an int dependent on another param (e.g. successes from trials)."""
    depends_on = spec.get("depends_on", "")
    base_val = ctx.get(depends_on, 50)
    ensure = spec.get("ensure", {})
    min_ratio = ensure.get("min_ratio", 0.1)
    max_ratio = ensure.get("max_ratio", 0.9)
    lo = max(1, int(base_val * min_ratio))
    hi = int(base_val * max_ratio)
    return rng.randint(lo, hi)
