"""Tests for Adventurer Tier System — Pantheon Prestige.

Covers:
  - get_tier: correct tier at boundaries and mid-range
  - get_next_tier: returns next or None at max
  - tier_progress: percentage, bounds, max tier, pantheon info
  - detect_tier_up: crossing detection
  - Tier data integrity (all tiers valid, ordered, unique)
  - Pantheon helpers: get_pantheon, completed_pantheons, pantheon_tiers, detect_pantheon_up
"""

import pytest

from app.services.tiers import (
    TIERS,
    Tier,
    Pantheon,
    PANTHEONS,
    get_tier,
    get_next_tier,
    tier_progress,
    detect_tier_up,
    get_pantheon,
    get_pantheon_for_tier,
    completed_pantheons,
    pantheon_tiers,
    detect_pantheon_up,
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

    def test_max_greek_tier(self):
        t = get_tier(4000)
        assert t.title == "Heir of Olympus"
        assert t.rank == 8
        assert t.pantheon == "greek"

    def test_first_norse_tier(self):
        t = get_tier(4500)
        assert t.title == "Thrall of Midgard"
        assert t.rank == 9
        assert t.pantheon == "norse"

    def test_between_greek_and_norse(self):
        """XP between Greek cap and Norse start stays at Greek max."""
        t = get_tier(4200)
        assert t.title == "Heir of Olympus"
        assert t.pantheon == "greek"

    def test_max_norse_tier(self):
        t = get_tier(27000)
        assert t.title == "Allfather's Heir"
        assert t.rank == 17
        assert t.pantheon == "norse"

    def test_first_egyptian_tier(self):
        t = get_tier(32500)
        assert t.title == "Scribe of the Nile"
        assert t.rank == 18
        assert t.pantheon == "egyptian"

    def test_max_tier_overall(self):
        t = get_tier(200000)
        assert t.title == "Child of the Stars"
        assert t.rank == 26
        assert t.pantheon == "egyptian"

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
        nxt = get_next_tier(102000)
        assert nxt is None

    def test_mid_tier_next(self):
        nxt = get_next_tier(650)
        assert nxt is not None
        assert nxt.title == "Artisan of Hephaestus"

    def test_greek_cap_next_is_norse(self):
        nxt = get_next_tier(4000)
        assert nxt is not None
        assert nxt.title == "Thrall of Midgard"
        assert nxt.pantheon == "norse"

    def test_norse_cap_next_is_egyptian(self):
        nxt = get_next_tier(27000)
        assert nxt is not None
        assert nxt.title == "Scribe of the Nile"
        assert nxt.pantheon == "egyptian"


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
        tp = tier_progress(150000)
        assert tp["current"].rank == 26
        assert tp["next"] is None
        assert tp["pct"] == 100

    def test_includes_pantheon_info(self):
        tp = tier_progress(500)
        assert tp["pantheon"].key == "greek"
        assert isinstance(tp["completed_pantheons"], list)
        assert len(tp["completed_pantheons"]) == 0

    def test_norse_progress_has_completed_greek(self):
        tp = tier_progress(5000)
        assert tp["pantheon"].key == "norse"
        assert len(tp["completed_pantheons"]) == 1
        assert tp["completed_pantheons"][0].key == "greek"

    def test_egyptian_progress_has_completed_both(self):
        tp = tier_progress(40000)
        assert tp["pantheon"].key == "egyptian"
        assert len(tp["completed_pantheons"]) == 2


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

    def test_cross_pantheon_boundary(self):
        result = detect_tier_up(4000, 4500)
        assert result is not None
        assert result.title == "Thrall of Midgard"
        assert result.pantheon == "norse"


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

    def test_27_tiers_total(self):
        assert len(TIERS) == 27

    def test_9_tiers_per_pantheon(self):
        for p_key in ("greek", "norse", "egyptian"):
            count = sum(1 for t in TIERS if t.pantheon == p_key)
            assert count == 9, f"Pantheon {p_key} has {count} tiers, expected 9"

    def test_all_tiers_have_valid_pantheon(self):
        valid = {"greek", "norse", "egyptian"}
        for t in TIERS:
            assert t.pantheon in valid, f"Tier {t.title} has invalid pantheon {t.pantheon}"


class TestPantheonHelpers:
    """Tests for pantheon helper functions."""

    def test_three_pantheons(self):
        assert len(PANTHEONS) == 3
        assert PANTHEONS[0].key == "greek"
        assert PANTHEONS[1].key == "norse"
        assert PANTHEONS[2].key == "egyptian"

    def test_get_pantheon_greek(self):
        p = get_pantheon(500)
        assert p.key == "greek"
        assert p.name == "Greek"

    def test_get_pantheon_norse(self):
        p = get_pantheon(5000)
        assert p.key == "norse"

    def test_get_pantheon_egyptian(self):
        p = get_pantheon(35000)
        assert p.key == "egyptian"

    def test_get_pantheon_between_greek_norse(self):
        """XP between Greek cap and Norse start is still Greek pantheon."""
        p = get_pantheon(4200)
        assert p.key == "greek"

    def test_get_pantheon_for_tier(self):
        norse_tier = TIERS[10]
        p = get_pantheon_for_tier(norse_tier)
        assert p.key == "norse"

    def test_completed_pantheons_none(self):
        result = completed_pantheons(500)
        assert result == []

    def test_completed_pantheons_greek(self):
        result = completed_pantheons(5000)
        assert len(result) == 1
        assert result[0].key == "greek"

    def test_completed_pantheons_greek_and_norse(self):
        result = completed_pantheons(35000)
        assert len(result) == 2
        assert result[0].key == "greek"
        assert result[1].key == "norse"

    def test_pantheon_tiers_returns_correct_count(self):
        greek = pantheon_tiers("greek")
        assert len(greek) == 9
        assert all(t.pantheon == "greek" for t in greek)

    def test_pantheon_tiers_norse_ordered(self):
        norse = pantheon_tiers("norse")
        assert norse[0].title == "Thrall of Midgard"
        assert norse[-1].title == "Allfather's Heir"

    def test_detect_pantheon_up_within_greek(self):
        result = detect_pantheon_up(50, 200)
        assert result is None

    def test_detect_pantheon_up_greek_to_norse(self):
        result = detect_pantheon_up(4000, 4500)
        assert result is not None
        assert result.key == "norse"

    def test_detect_pantheon_up_norse_to_egyptian(self):
        result = detect_pantheon_up(27000, 32500)
        assert result is not None
        assert result.key == "egyptian"

    def test_detect_pantheon_up_no_change(self):
        result = detect_pantheon_up(5000, 7000)
        assert result is None

    def test_detect_pantheon_up_xp_decrease(self):
        result = detect_pantheon_up(5000, 3000)
        assert result is None
