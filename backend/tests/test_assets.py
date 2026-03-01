"""Tests for asset rendering (tables, charts, spinners)."""

import pytest

from app.services.assets import render_assets


class TestTableRendering:
    def test_table_from_categories(self):
        """Render a table from a categories dict (pie chart question)."""
        spec = [{
            "kind": "table",
            "id": "snack_table",
            "title": "Number of students choosing each snack",
            "columns": ["Snack", "Count"],
            "rows_from": "categories",
        }]
        params = {
            "categories": {
                "labels": ["Fruit", "Crisps", "Chocolate"],
                "counts": [8, 12, 4],
                "total": 24,
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 1
        assert result[0]["id"] == "snack_table"
        assert result[0]["kind"] == "table"
        html = result[0]["html"]
        assert "<table" in html
        assert "Fruit" in html
        assert "Crisps" in html
        assert "12" in html

    def test_table_with_static_rows_and_expressions(self):
        """Render a table with static rows containing {param} references."""
        spec = [{
            "kind": "table",
            "id": "exp_table",
            "title": "Results",
            "columns": ["Outcome", "Count"],
            "rows": [
                ["{success_label}", "{successes}"],
                ["Other", "{trials - successes}"],
            ],
        }]
        params = {
            "trials": 50,
            "successes": 15,
            "success_label": "red",
        }
        result = render_assets(spec, params)
        assert len(result) == 1
        html = result[0]["html"]
        assert "red" in html
        assert "15" in html
        assert "35" in html  # 50 - 15

    def test_empty_table(self):
        spec = [{
            "kind": "table",
            "id": "t",
            "columns": ["A"],
            "rows": [],
        }]
        result = render_assets(spec, {})
        assert len(result) == 1
        assert "<table" in result[0]["html"]


class TestLineChart:
    def test_renders_svg(self):
        spec = [{
            "kind": "chart",
            "id": "line_chart",
            "chart_type": "line",
            "title": "Data over the week",
            "x": "dataset.x",
            "y": "dataset.y",
        }]
        params = {
            "dataset": {
                "x": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                "y": [10, 25, 30, 15, 20],
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 1
        html = result[0]["html"]
        assert "<svg" in html
        assert "polyline" in html
        assert "Mon" in html
        assert "Fri" in html

    def test_single_point(self):
        spec = [{
            "kind": "chart",
            "id": "lc",
            "chart_type": "line",
            "x": "dataset.x",
            "y": "dataset.y",
        }]
        params = {"dataset": {"x": ["A"], "y": [5]}}
        result = render_assets(spec, params)
        assert "<svg" in result[0]["html"]


class TestPieChart:
    def test_renders_svg(self):
        spec = [{
            "kind": "chart",
            "id": "pie",
            "chart_type": "pie",
            "data_from": "categories",
        }]
        params = {
            "categories": {
                "labels": ["A", "B", "C"],
                "counts": [10, 20, 30],
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 1
        html = result[0]["html"]
        assert "<svg" in html
        assert "<path" in html
        assert "A (10)" in html


class TestSpinner:
    def test_renders_svg(self):
        spec = [{
            "kind": "chart",
            "id": "spinner",
            "chart_type": "spinner",
            "sectors_from": "scenario.sectors",
        }]
        params = {
            "scenario": {
                "sectors": ["red", "blue", "red", "green"],
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 1
        html = result[0]["html"]
        assert "<svg" in html
        assert "red" in html
        assert "blue" in html

    def test_spinner_with_no_data(self):
        spec = [{
            "kind": "chart",
            "id": "spinner",
            "chart_type": "spinner",
            "sectors_from": "missing",
        }]
        result = render_assets(spec, {"missing": []})
        assert "unavailable" in result[0]["html"].lower()


class TestConditionalRendering:
    def test_when_true_renders(self):
        spec = [{
            "kind": "chart",
            "id": "spinner",
            "chart_type": "spinner",
            "when": "scenario.object_name == 'spinner'",
            "sectors_from": "scenario.sectors",
        }]
        params = {
            "scenario": {
                "object_name": "spinner",
                "sectors": ["red", "blue"],
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 1

    def test_when_false_skips(self):
        spec = [{
            "kind": "chart",
            "id": "spinner",
            "chart_type": "spinner",
            "when": "scenario.object_name == 'spinner'",
            "sectors_from": "scenario.sectors",
        }]
        params = {
            "scenario": {
                "object_name": "die",
                "sectors": [],
            }
        }
        result = render_assets(spec, params)
        assert len(result) == 0

    def test_no_when_always_renders(self):
        spec = [{"kind": "table", "id": "t", "columns": ["X"], "rows": []}]
        result = render_assets(spec, {})
        assert len(result) == 1


class TestMultipleAssets:
    def test_renders_all(self):
        specs = [
            {"kind": "table", "id": "t1", "columns": ["A"], "rows": [["1"]]},
            {"kind": "table", "id": "t2", "columns": ["B"], "rows": [["2"]]},
        ]
        result = render_assets(specs, {})
        assert len(result) == 2
        assert result[0]["id"] == "t1"
        assert result[1]["id"] == "t2"
