"""Marking engine – validates student answers against the correct answer.

Each marking mode is registered as a function that receives:
  - student_answer: str  (always raw string from the form)
  - correct: Any         (the expected answer, any type)
  - spec: dict           (the marking spec from the template)
Returns a MarkResult.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable


@dataclass
class MarkResult:
    correct: bool
    score: float        # 0.0 – 1.0 (partial credit possible)
    feedback: str       # short feedback string
    expected: str       # canonical expected answer for display


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_MARKERS: dict[str, Callable] = {}


def register_marker(mode: str):
    def decorator(fn):
        _MARKERS[mode] = fn
        return fn
    return decorator


def mark(student_answer: str, correct: Any, spec: dict) -> MarkResult:
    """Dispatch to the correct marking function."""
    mode = spec.get("mode")
    if mode not in _MARKERS:
        raise ValueError(f"Unknown marking mode: {mode}")
    return _MARKERS[mode](student_answer.strip(), correct, spec)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _try_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _try_fraction(s: str) -> Fraction | None:
    """Try to parse '3/4', '3 / 4', etc."""
    s = s.replace(" ", "")
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 2:
            try:
                return Fraction(int(parts[0]), int(parts[1]))
            except (ValueError, ZeroDivisionError):
                return None
    # Also support decimals as Fraction
    try:
        return Fraction(s).limit_denominator(10000)
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# Mode: exact_numeric
# ---------------------------------------------------------------------------

@register_marker("exact_numeric")
def mark_exact_numeric(student: str, correct: Any, spec: dict) -> MarkResult:
    expected_val = float(correct)
    student_val = _try_float(student)
    expected_str = str(correct)

    if student_val is None:
        return MarkResult(False, 0.0, "Your answer must be a number.", expected_str)

    if math.isclose(student_val, expected_val, abs_tol=1e-9):
        return MarkResult(True, 1.0, "Correct!", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


# ---------------------------------------------------------------------------
# Mode: exact_text_normalised
# ---------------------------------------------------------------------------

@register_marker("exact_text_normalised")
def mark_exact_text(student: str, correct: Any, spec: dict) -> MarkResult:
    expected_str = str(correct)
    # Normalise: lowercase, strip whitespace
    norm_student = re.sub(r"\s+", " ", student.lower().strip())
    norm_expected = re.sub(r"\s+", " ", expected_str.lower().strip())

    if norm_student == norm_expected:
        return MarkResult(True, 1.0, "Correct!", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


# ---------------------------------------------------------------------------
# Mode: numeric_tolerance
# ---------------------------------------------------------------------------

@register_marker("numeric_tolerance")
def mark_numeric_tolerance(student: str, correct: Any, spec: dict) -> MarkResult:
    expected_val = float(correct)
    student_val = _try_float(student)
    expected_str = str(correct)
    tol = spec.get("tolerance", 0.01)

    if student_val is None:
        return MarkResult(False, 0.0, "Your answer must be a number.", expected_str)

    if math.isclose(student_val, expected_val, abs_tol=tol):
        return MarkResult(True, 1.0, "Correct!", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


# ---------------------------------------------------------------------------
# Mode: rounding_dp
# ---------------------------------------------------------------------------

@register_marker("rounding_dp")
def mark_rounding_dp(student: str, correct: Any, spec: dict) -> MarkResult:
    # dp is resolved by check_answer into spec["dp"]; fall back to spec["dp"] default
    dp = spec.get("dp", 2)
    dp = int(dp)
    expected_val = round(float(correct), dp)
    expected_str = f"{expected_val:.{dp}f}"

    student_val = _try_float(student)
    if student_val is None:
        return MarkResult(False, 0.0, "Your answer must be a number.", expected_str)

    # Check value is correct
    if not math.isclose(student_val, expected_val, abs_tol=10 ** (-(dp + 2))):
        return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)

    # Check format — count decimal places in student answer
    if "." in student:
        student_dp = len(student.rstrip("0").split(".")[1]) if student.rstrip("0").split(".")[1] else 0
        # Actually we need exact dp, not stripped
        student_dp_exact = len(student.split(".")[1])
        if student_dp_exact != dp:
            return MarkResult(
                True, 0.8,
                f"Correct value, but write it to exactly {dp} decimal places: {expected_str}.",
                expected_str,
            )
    elif dp > 0:
        return MarkResult(
            True, 0.8,
            f"Correct value, but write it to {dp} decimal places: {expected_str}.",
            expected_str,
        )

    return MarkResult(True, 1.0, "Correct!", expected_str)


# ---------------------------------------------------------------------------
# Mode: fraction_or_decimal
# ---------------------------------------------------------------------------

@register_marker("fraction_or_decimal")
def mark_fraction_or_decimal(student: str, correct: Any, spec: dict) -> MarkResult:
    # correct may be a Fraction, float, or string
    if isinstance(correct, Fraction):
        expected_frac = correct
    elif isinstance(correct, (int, float)):
        expected_frac = Fraction(correct).limit_denominator(10000)
    else:
        expected_frac = _try_fraction(str(correct))
        if expected_frac is None:
            expected_frac = Fraction(0)

    expected_str = str(expected_frac)
    accepted = spec.get("accepted_forms", ["fraction_simplified", "decimal"])
    rounding = spec.get("rounding") or {}
    decimal_places = rounding.get("decimal_places")

    # Try parsing student answer as fraction
    student_frac = _try_fraction(student)
    student_float = _try_float(student)

    if student_frac is not None:
        # Check fraction equivalence
        if student_frac == expected_frac:
            return MarkResult(True, 1.0, "Correct!", expected_str)
        # Check if equivalent but not simplified
        if student_frac == expected_frac and "fraction_simplified" in accepted:
            # Already caught above
            pass
        # Unsimplified but equivalent?
        if Fraction(student_frac.numerator, student_frac.denominator) == expected_frac:
            return MarkResult(True, 1.0, "Correct!", expected_str)

    if student_float is not None:
        expected_float = float(expected_frac)
        if decimal_places is not None:
            # Round both and compare
            if math.isclose(round(student_float, decimal_places),
                            round(expected_float, decimal_places),
                            abs_tol=10 ** (-(decimal_places + 1))):
                return MarkResult(True, 1.0, "Correct!", expected_str)
        else:
            if math.isclose(student_float, expected_float, rel_tol=1e-6, abs_tol=1e-9):
                return MarkResult(True, 1.0, "Correct!", expected_str)

    if student_frac is None and student_float is None:
        return MarkResult(False, 0.0, "Enter a fraction (e.g. 3/10) or a decimal.", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


# ---------------------------------------------------------------------------
# Mode: remainder_form
# ---------------------------------------------------------------------------

_REMAINDER_RE = re.compile(r"(\d+)\s*[rR]\s*(\d+)")


@register_marker("remainder_form")
def mark_remainder_form(student: str, correct: Any, spec: dict) -> MarkResult:
    # correct is a dict {"quotient": int, "remainder": int} or a string "23 r 4"
    if isinstance(correct, dict):
        exp_q = correct["quotient"]
        exp_r = correct["remainder"]
    else:
        m = _REMAINDER_RE.match(str(correct))
        if m:
            exp_q, exp_r = int(m.group(1)), int(m.group(2))
        else:
            exp_q, exp_r = 0, 0

    expected_str = f"{exp_q} r {exp_r}"

    m = _REMAINDER_RE.match(student)
    if m is None:
        return MarkResult(False, 0.0,
                          "Write your answer as a whole number with remainder, e.g. '23 r 4'.",
                          expected_str)

    sq, sr = int(m.group(1)), int(m.group(2))
    if sq == exp_q and sr == exp_r:
        return MarkResult(True, 1.0, "Correct!", expected_str)

    if sq == exp_q:
        return MarkResult(False, 0.0, f"Quotient is right but check the remainder.", expected_str)
    if sr == exp_r:
        return MarkResult(False, 0.0, f"Remainder is right but check the quotient.", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


# ---------------------------------------------------------------------------
# Mode: algebra_normal_form
# ---------------------------------------------------------------------------

_ALGEBRA_TERM_RE = re.compile(r"([+-]?\s*\d*)\s*([a-zA-Z])?")


@register_marker("algebra_normal_form")
def mark_algebra_normal_form(student: str, correct: Any, spec: dict) -> MarkResult:
    """Check algebraic simplification like '3a', '-2a', '0', etc."""
    variable = spec.get("variable", "a")

    # Parse expected
    if isinstance(correct, dict):
        exp_coeff = correct.get("total_coeff", 0)
    elif isinstance(correct, (int, float)):
        exp_coeff = int(correct)
    else:
        exp_coeff = _parse_algebra_coeff(str(correct), variable)

    if exp_coeff == 0:
        expected_str = "0"
    elif exp_coeff == 1:
        expected_str = variable
    elif exp_coeff == -1:
        expected_str = f"-{variable}"
    else:
        expected_str = f"{exp_coeff}{variable}"

    # Parse student answer
    student_coeff = _parse_algebra_coeff(student, variable)
    if student_coeff is None:
        return MarkResult(False, 0.0,
                          f"Write your answer in terms of {variable}, e.g. '3{variable}' or '-2{variable}'.",
                          expected_str)

    if student_coeff == exp_coeff:
        return MarkResult(True, 1.0, "Correct!", expected_str)

    return MarkResult(False, 0.0, f"Not quite. The answer is {expected_str}.", expected_str)


def _parse_algebra_coeff(s: str, var: str) -> int | None:
    """Parse '3a', '-2a', 'a', '-a', '0' → coefficient integer."""
    s = s.strip().replace(" ", "")
    if not s:
        return None

    # Just "0"
    if s == "0":
        return 0

    # Contains variable?
    if var in s:
        coeff_str = s.replace(var, "")
        if coeff_str == "" or coeff_str == "+":
            return 1
        if coeff_str == "-":
            return -1
        try:
            return int(coeff_str)
        except ValueError:
            return None

    # No variable — should be 0 or a plain number (0 coefficient expected)
    try:
        val = int(s)
        return val  # Treat as "coeff" (if expected is 0, this matches)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Mode: order_match
# ---------------------------------------------------------------------------

@register_marker("order_match")
def mark_order_match(student: str, correct: Any, spec: dict) -> MarkResult:
    """Student provides ordered list; check if it matches the correct order.
    Student answer can be comma/newline-separated or JSON list.
    """
    if isinstance(correct, list):
        expected_list = [str(x).strip().lower() for x in correct]
    else:
        expected_list = [s.strip().lower() for s in str(correct).split(",")]

    expected_str = ", ".join(expected_list)

    # Parse student answer
    import json
    try:
        student_list = json.loads(student)
        if isinstance(student_list, list):
            student_list = [str(x).strip().lower() for x in student_list]
        else:
            student_list = None
    except (json.JSONDecodeError, TypeError):
        student_list = None

    if student_list is None:
        # Try comma or newline split
        sep = "," if "," in student else "\n"
        student_list = [s.strip().lower() for s in student.split(sep) if s.strip()]

    if len(student_list) != len(expected_list):
        return MarkResult(False, 0.0,
                          f"Expected {len(expected_list)} items in your ordering.",
                          expected_str)

    if student_list == expected_list:
        return MarkResult(True, 1.0, "Correct!", expected_str)

    # Partial credit: count items in correct position
    correct_positions = sum(1 for a, b in zip(student_list, expected_list) if a == b)
    partial = correct_positions / len(expected_list)

    return MarkResult(False, partial,
                      f"Not quite. {correct_positions}/{len(expected_list)} in the right place.",
                      expected_str)


# ---------------------------------------------------------------------------
# Mode: mcq
# ---------------------------------------------------------------------------

@register_marker("mcq")
def mark_mcq(student: str, correct: Any, spec: dict) -> MarkResult:
    """Multi-choice: student picks the correct option label or text."""
    expected_str = str(correct).strip()

    # Compare normalised
    if student.lower().strip() == expected_str.lower().strip():
        return MarkResult(True, 1.0, "Correct!", expected_str)

    # Also accept option letter (A, B, C, D) if options are provided
    options = spec.get("options")
    if options and student.upper().strip() in ["A", "B", "C", "D"]:
        idx = ord(student.upper().strip()) - ord("A")
        if 0 <= idx < len(options) and str(options[idx]).lower().strip() == expected_str.lower().strip():
            return MarkResult(True, 1.0, "Correct!", expected_str)

    return MarkResult(False, 0.0, f"Not quite.", expected_str)
