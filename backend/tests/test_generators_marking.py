"""Tests for parameter generators and marking engine."""

import random
from fractions import Fraction

import pytest

from app.services.generators import generate_param
from app.services.marking import mark, MarkResult


# ===================================================================
# Generator tests
# ===================================================================


class TestGeneratorDeterminism:
    """Generators must produce the same output for the same seed."""

    def _gen(self, spec: dict, seed: int = 42, ctx: dict | None = None) -> any:
        rng = random.Random(seed)
        return generate_param(rng, spec, ctx or {})

    def test_int_deterministic(self):
        spec = {"gen": "int", "range": {"min": 1, "max": 100}}
        a = self._gen(spec, seed=42)
        b = self._gen(spec, seed=42)
        assert a == b
        assert isinstance(a, int)
        assert 1 <= a <= 100

    def test_decimal_deterministic(self):
        spec = {"gen": "decimal", "range": {"min": 0.1, "max": 10.0}, "dp": 2}
        a = self._gen(spec, seed=99)
        b = self._gen(spec, seed=99)
        assert a == b
        assert 0.1 <= a <= 10.0

    def test_int_list_deterministic(self):
        spec = {"gen": "int_list", "count": {"min": 5, "max": 5}, "range": {"min": 1, "max": 20}}
        a = self._gen(spec, seed=7)
        b = self._gen(spec, seed=7)
        assert a == b
        assert len(a) == 5

    def test_int_list_divisible_mean(self):
        spec = {
            "gen": "int_list",
            "count": {"min": 6, "max": 6},
            "range": {"min": 1, "max": 30},
            "ensure": {"divisible_mean": True},
        }
        values = self._gen(spec, seed=42)
        assert sum(values) % len(values) == 0

    def test_int_list_with_mode(self):
        spec = {
            "gen": "int_list_with_mode",
            "count": {"min": 8, "max": 8},
            "range": {"min": 1, "max": 15},
        }
        values = self._gen(spec, seed=42)
        assert len(values) == 8
        from collections import Counter
        c = Counter(values)
        mode_val, mode_count = c.most_common(1)[0]
        # Mode should appear more than any other value
        for val, count in c.items():
            if val != mode_val:
                assert count < mode_count

    def test_pick_one(self):
        spec = {"gen": "pick_one", "from": ["a", "b", "c"]}
        result = self._gen(spec, seed=42)
        assert result in ["a", "b", "c"]

    def test_categorical_counts(self):
        spec = {
            "gen": "categorical_counts",
            "labels": ["A", "B", "C"],
            "count_range": {"min": 3, "max": 15},
        }
        result = self._gen(spec, seed=42)
        assert "labels" in result
        assert "counts" in result
        assert len(result["labels"]) == 3
        assert len(result["counts"]) == 3

    def test_linear_expression(self):
        spec = {
            "gen": "linear_expression",
            "vars": ["x"],
            "coeff_range": {"min": -5, "max": 8},
            "const_range": {"min": -10, "max": 10},
        }
        result = self._gen(spec, seed=42)
        assert "expr_str" in result
        assert "coeffs" in result
        assert "x" in result["coeffs"]

    def test_like_terms(self):
        spec = {
            "gen": "like_terms_expression",
            "var": "a",
            "term_count": {"min": 4, "max": 4},
            "coeff_range": {"min": -9, "max": 9},
            "ensure": {"has_both_signs": True},
        }
        result = self._gen(spec, seed=42)
        assert "expr_str" in result
        assert "total_coeff" in result
        assert result["total_coeff"] == sum(result["coeffs"])

    def test_metric_conversion(self):
        spec = {"gen": "metric_conversion"}
        result = self._gen(spec, seed=42)
        assert "from_unit" in result
        assert "to_unit" in result
        assert result["from_unit"] != result["to_unit"]

    def test_arithmetic_expression(self):
        spec = {"gen": "arithmetic_expression"}
        result = self._gen(spec, seed=42)
        assert "expr_str" in result
        assert "result" in result
        assert isinstance(result["result"], int)

    def test_equally_likely_scenario(self):
        spec = {"gen": "equally_likely_scenario", "types": ["die", "coin", "spinner"]}
        result = self._gen(spec, seed=42)
        assert "object_name" in result
        assert "probability" in result
        assert isinstance(result["probability"], Fraction)

    def test_probability_fraction(self):
        spec = {"gen": "probability_fraction", "denom": 10, "ensure": {"min": 1, "max": 5}}
        result = self._gen(spec, seed=42)
        assert isinstance(result, Fraction)
        assert 0 < float(result) <= 0.5


# ===================================================================
# Marking tests
# ===================================================================


class TestExactNumeric:
    def test_correct_integer(self):
        r = mark("42", 42, {"mode": "exact_numeric"})
        assert r.correct
        assert r.score == 1.0

    def test_correct_float(self):
        r = mark("3.5", 3.5, {"mode": "exact_numeric"})
        assert r.correct

    def test_incorrect(self):
        r = mark("43", 42, {"mode": "exact_numeric"})
        assert not r.correct

    def test_non_numeric_answer(self):
        r = mark("abc", 42, {"mode": "exact_numeric"})
        assert not r.correct
        assert "number" in r.feedback.lower()


class TestExactTextNormalised:
    def test_exact_match(self):
        r = mark("hello", "hello", {"mode": "exact_text_normalised"})
        assert r.correct

    def test_case_insensitive(self):
        r = mark("HELLO", "hello", {"mode": "exact_text_normalised"})
        assert r.correct

    def test_whitespace_normalised(self):
        r = mark("  hello  world ", "hello world", {"mode": "exact_text_normalised"})
        assert r.correct

    def test_wrong(self):
        r = mark("goodbye", "hello", {"mode": "exact_text_normalised"})
        assert not r.correct


class TestNumericTolerance:
    def test_exact(self):
        r = mark("3.14", 3.14, {"mode": "numeric_tolerance", "tolerance": 0.01})
        assert r.correct

    def test_within_tolerance(self):
        r = mark("3.145", 3.14, {"mode": "numeric_tolerance", "tolerance": 0.01})
        assert r.correct

    def test_outside_tolerance(self):
        r = mark("3.20", 3.14, {"mode": "numeric_tolerance", "tolerance": 0.01})
        assert not r.correct


class TestRoundingDp:
    def test_correct_1dp(self):
        r = mark("3.1", 3.14159, {"mode": "rounding_dp", "dp": 1})
        assert r.correct
        assert r.score == 1.0

    def test_correct_2dp(self):
        r = mark("3.14", 3.14159, {"mode": "rounding_dp", "dp": 2})
        assert r.correct

    def test_wrong_rounding(self):
        r = mark("3.15", 3.14159, {"mode": "rounding_dp", "dp": 2})
        assert not r.correct

    def test_correct_value_wrong_format(self):
        """Correct value but shown as integer when dp > 0."""
        r = mark("3", 3.0, {"mode": "rounding_dp", "dp": 1})
        assert r.correct  # value is right
        assert r.score < 1.0  # but format penalty


class TestFractionOrDecimal:
    def test_fraction_correct(self):
        r = mark("1/2", Fraction(1, 2), {"mode": "fraction_or_decimal"})
        assert r.correct

    def test_decimal_correct(self):
        r = mark("0.5", Fraction(1, 2), {"mode": "fraction_or_decimal"})
        assert r.correct

    def test_unsimplified_fraction(self):
        r = mark("2/4", Fraction(1, 2), {"mode": "fraction_or_decimal"})
        assert r.correct

    def test_wrong_fraction(self):
        r = mark("1/3", Fraction(1, 2), {"mode": "fraction_or_decimal"})
        assert not r.correct

    def test_invalid_input(self):
        r = mark("abc", Fraction(1, 2), {"mode": "fraction_or_decimal"})
        assert not r.correct


class TestRemainderForm:
    def test_correct(self):
        r = mark("23 r 4", {"quotient": 23, "remainder": 4}, {"mode": "remainder_form"})
        assert r.correct

    def test_uppercase_R(self):
        r = mark("23 R 4", {"quotient": 23, "remainder": 4}, {"mode": "remainder_form"})
        assert r.correct

    def test_wrong_remainder(self):
        r = mark("23 r 5", {"quotient": 23, "remainder": 4}, {"mode": "remainder_form"})
        assert not r.correct
        assert "remainder" in r.feedback.lower()

    def test_wrong_quotient(self):
        r = mark("22 r 4", {"quotient": 23, "remainder": 4}, {"mode": "remainder_form"})
        assert not r.correct
        assert "quotient" in r.feedback.lower()

    def test_bad_format(self):
        r = mark("23.4", {"quotient": 23, "remainder": 4}, {"mode": "remainder_form"})
        assert not r.correct


class TestAlgebraNormalForm:
    def test_positive_coeff(self):
        r = mark("3a", {"total_coeff": 3}, {"mode": "algebra_normal_form", "variable": "a"})
        assert r.correct

    def test_negative_coeff(self):
        r = mark("-2a", {"total_coeff": -2}, {"mode": "algebra_normal_form", "variable": "a"})
        assert r.correct

    def test_coeff_one(self):
        r = mark("a", {"total_coeff": 1}, {"mode": "algebra_normal_form", "variable": "a"})
        assert r.correct

    def test_coeff_negative_one(self):
        r = mark("-a", {"total_coeff": -1}, {"mode": "algebra_normal_form", "variable": "a"})
        assert r.correct

    def test_zero(self):
        r = mark("0", {"total_coeff": 0}, {"mode": "algebra_normal_form", "variable": "a"})
        assert r.correct

    def test_wrong(self):
        r = mark("4a", {"total_coeff": 3}, {"mode": "algebra_normal_form", "variable": "a"})
        assert not r.correct


class TestOrderMatch:
    def test_correct_order(self):
        r = mark("a, b, c", ["a", "b", "c"], {"mode": "order_match"})
        assert r.correct

    def test_wrong_order(self):
        r = mark("c, b, a", ["a", "b", "c"], {"mode": "order_match"})
        assert not r.correct

    def test_partial_credit(self):
        r = mark("a, c, b", ["a", "b", "c"], {"mode": "order_match"})
        assert not r.correct
        assert r.score > 0  # partial credit for 'a' in right place


class TestMcq:
    def test_correct_text(self):
        r = mark("Paris", "Paris", {"mode": "mcq"})
        assert r.correct

    def test_case_insensitive(self):
        r = mark("paris", "Paris", {"mode": "mcq"})
        assert r.correct

    def test_wrong(self):
        r = mark("London", "Paris", {"mode": "mcq"})
        assert not r.correct
