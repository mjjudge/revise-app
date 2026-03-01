"""Tests for EPIC 6.7 — Adventurer Tier System.

Covers:
  - get_tier: correct tier at boundaries and mid-range
  - get_next_tier: returns next or None at max
  - tier_progress: percentage, bounds, max tier
  - detect_tier_up: crossing detection
  - Tier data integrity (all tiers valid, ordered, unique)
"""

import pytest

from app.services.tiers import (
    TIERS,
    Tier,
    get_tier,
    get_next_tier,
    tier_progress,
    detect_tier_up,
)


class TestGetTier:
    """Tests for get_tier()."""

    def test_zero_xp_is_mortal(self):
        t = get_tier(0)
        assert t.title == "Mortal"
        assert t.rank == 0

    def test_exact_boundary_100(self):
        t = get_tier(100)
        assert t.title == "Acolyte of Athena"
        assert t.rank == 1

    def test_just_below_boundary(self):
        t = get_tier(99)
        assert t.title == "Mortal"
        assert t.rank == 0

    def test_mid_range(self):
        t = get_tier(450)
        assert t.title == "Messenger of Hermes"
        assert t.rank == 2

    def test_max_tier(self):
        t = get_tier(10000)
        assert t.title == "Heir of Olympus"
        assert t.rank == 8

    def test_exact_max_threshold(self):
        t = get_tier(4000)
        assert t.title == "Heir of Olympus"

    def test_each_tier_at_threshold(self):
        """Every tier is reachable at its exact xp_required."""
        for tier in TIERS:
            result = get_tier(tier.xp_required)
            assert result.rank == tier.rank, (
                f"At XP {tier.xp_required}, expected rank {tier.rank} "
                f"({tier.title}), got rank {result.rank} ({result.title})"
            )


class TestGetNextTier:
    """Tests for get_next_tier()."""

    def test_mortal_next_is_athena(self):
        nxt = get_next_tier(0)
        assert nxt is not None
        assert nxt.title == "Acolyte of Athena"

    def test_max_tier_has_no_next(self):
        nxt = get_next_tier(4000)
        assert nxt is None

    def test_mid_tier_next(self):
        nxt = get_next_tier(650)
        assert nxt is not None
        assert nxt.title == "Artisan of Hephaestus"


class TestTierProgress:
    """Tests for tier_progress()."""

    def test_zero_xp_progress(self):
        tp = tier_progress(0)
        assert tp["current"].rank == 0
        assert tp["next"].rank == 1
        assert tp["pct"] == 0
        assert tp["xp_into_tier"] == 0
        assert tp["xp_needed"] == 100

    def test_halfway_progress(self):
        tp = tier_progress(50)
        assert tp["pct"] == 50

    def test_near_boundary(self):
        tp = tier_progress(99)
        assert tp["pct"] == 99

    def test_at_boundary(self):
        tp = tier_progress(100)
        assert tp["current"].rank == 1
        assert tp["next"].rank == 2
        assert tp["xp_into_tier"] == 0

    def test_max_tier_progress(self):
        tp = tier_progress(5000)
        assert tp["current"].rank == 8
        assert tp["next"] is None
        assert tp["pct"] == 100


class TestDetectTierUp:
    """Tests for detect_tier_up()."""

    def test_no_tier_up_within_same(self):
        result = detect_tier_up(10, 50)
        assert result is None

    def test_tier_up_crossing_boundary(self):
        result = detect_tier_up(90, 110)
        assert result is not None
        assert result.title == "Acolyte of Athena"

    def test_exact_boundary(self):
        result = detect_tier_up(99, 100)
        assert result is not None
        assert result.rank == 1

    def test_no_xp_gain(self):
        result = detect_tier_up(100, 100)
        assert result is None

    def test_xp_decrease(self):
        result = detect_tier_up(300, 200)
        assert result is None

    def test_multi_tier_jump(self):
        """Jumping across multiple tiers returns the highest new tier."""
        result = detect_tier_up(0, 4000)
        assert result is not None
        assert result.title == "Heir of Olympus"


class TestTierDataIntegrity:
    """Validate the tier definitions themselves."""

    def test_tiers_ordered_by_xp(self):
        for i in range(1, len(TIERS)):
            assert TIERS[i].xp_required > TIERS[i - 1].xp_required, (
                f"Tier {TIERS[i].title} xp_required ({TIERS[i].xp_required}) "
                f"not greater than {TIERS[i-1].title} ({TIERS[i-1].xp_required})"
            )

    def test_ranks_sequential(self):
        for i, tier in enumerate(TIERS):
            assert tier.rank == i

    def test_unique_titles(self):
        titles = [t.title for t in TIERS]
        assert len(titles) == len(set(titles))

    def test_first_tier_starts_at_zero(self):
        assert TIERS[0].xp_required == 0

    def test_all_tiers_have_colours(self):
        for t in TIERS:
            assert t.accent, f"Tier {t.title} missing accent"
            assert t.glow, f"Tier {t.title} missing glow"
            assert t.gradient_from, f"Tier {t.title} missing gradient_from"
            assert t.badge_bg, f"Tier {t.title} missing badge_bg"

    def test_all_tiers_have_flavour(self):
        for t in TIERS:
            assert len(t.flavour) > 10, f"Tier {t.title} flavour too short"

    def test_at_least_5_tiers(self):
        assert len(TIERS) >= 5
