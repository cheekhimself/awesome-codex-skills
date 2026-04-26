#!/usr/bin/env python3
"""Tests for slack-gif-creator/core/easing.py"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.easing import (
    EASING_FUNCTIONS,
    apply_squash_stretch,
    calculate_arc_motion,
    ease_back_in,
    ease_back_in_out,
    ease_back_out,
    ease_in_bounce,
    ease_in_cubic,
    ease_in_elastic,
    ease_in_out_bounce,
    ease_in_out_cubic,
    ease_in_out_elastic,
    ease_in_out_quad,
    ease_in_quad,
    ease_out_bounce,
    ease_out_cubic,
    ease_out_elastic,
    ease_out_quad,
    get_easing,
    interpolate,
    linear,
)


# ---------------------------------------------------------------------------
# Boundary value helpers
# ---------------------------------------------------------------------------

def _boundary_ok(fn):
    """All easing functions must return 0 at t=0 and 1 at t=1."""
    assert fn(0) == pytest.approx(0.0, abs=1e-9)
    assert fn(1) == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# linear
# ---------------------------------------------------------------------------

class TestLinear:
    def test_identity(self):
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert linear(t) == pytest.approx(t)

    def test_boundaries(self):
        _boundary_ok(linear)


# ---------------------------------------------------------------------------
# Quad family
# ---------------------------------------------------------------------------

class TestEaseInQuad:
    def test_boundaries(self):
        _boundary_ok(ease_in_quad)

    def test_slow_start(self):
        # ease-in means output < input for 0 < t < 1
        assert ease_in_quad(0.5) < 0.5

    def test_midpoint(self):
        assert ease_in_quad(0.5) == pytest.approx(0.25)


class TestEaseOutQuad:
    def test_boundaries(self):
        _boundary_ok(ease_out_quad)

    def test_fast_start(self):
        # ease-out means output > input for 0 < t < 1
        assert ease_out_quad(0.5) > 0.5

    def test_midpoint(self):
        assert ease_out_quad(0.5) == pytest.approx(0.75)


class TestEaseInOutQuad:
    def test_boundaries(self):
        _boundary_ok(ease_in_out_quad)

    def test_midpoint_is_half(self):
        assert ease_in_out_quad(0.5) == pytest.approx(0.5)

    def test_symmetry(self):
        # f(t) + f(1-t) == 1 for smooth ease-in-out
        for t in [0.1, 0.3, 0.7, 0.9]:
            assert ease_in_out_quad(t) + ease_in_out_quad(1 - t) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Cubic family
# ---------------------------------------------------------------------------

class TestEaseInCubic:
    def test_boundaries(self):
        _boundary_ok(ease_in_cubic)

    def test_midpoint(self):
        assert ease_in_cubic(0.5) == pytest.approx(0.125)


class TestEaseOutCubic:
    def test_boundaries(self):
        _boundary_ok(ease_out_cubic)

    def test_midpoint(self):
        assert ease_out_cubic(0.5) == pytest.approx(0.875)


class TestEaseInOutCubic:
    def test_boundaries(self):
        _boundary_ok(ease_in_out_cubic)

    def test_midpoint_is_half(self):
        assert ease_in_out_cubic(0.5) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Bounce family
# ---------------------------------------------------------------------------

class TestEaseOutBounce:
    def test_boundaries(self):
        _boundary_ok(ease_out_bounce)

    def test_all_outputs_in_range(self):
        for i in range(101):
            t = i / 100
            result = ease_out_bounce(t)
            assert -0.05 <= result <= 1.05, f"out-of-range at t={t}: {result}"


class TestEaseInBounce:
    def test_boundaries(self):
        _boundary_ok(ease_in_bounce)

    def test_complement(self):
        # ease_in_bounce(t) == 1 - ease_out_bounce(1-t)
        for i in range(1, 10):
            t = i / 10
            assert ease_in_bounce(t) == pytest.approx(1 - ease_out_bounce(1 - t))


class TestEaseInOutBounce:
    def test_boundaries(self):
        _boundary_ok(ease_in_out_bounce)

    def test_midpoint_is_half(self):
        assert ease_in_out_bounce(0.5) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Elastic family
# ---------------------------------------------------------------------------

class TestEaseInElastic:
    def test_boundary_zero(self):
        assert ease_in_elastic(0) == pytest.approx(0.0)

    def test_boundary_one(self):
        assert ease_in_elastic(1) == pytest.approx(1.0)


class TestEaseOutElastic:
    def test_boundary_zero(self):
        assert ease_out_elastic(0) == pytest.approx(0.0)

    def test_boundary_one(self):
        assert ease_out_elastic(1) == pytest.approx(1.0)


class TestEaseInOutElastic:
    def test_boundary_zero(self):
        assert ease_in_out_elastic(0) == pytest.approx(0.0)

    def test_boundary_one(self):
        assert ease_in_out_elastic(1) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Back family
# ---------------------------------------------------------------------------

class TestEaseBackIn:
    def test_boundaries(self):
        _boundary_ok(ease_back_in)

    def test_slight_undershoot(self):
        # back-in goes slightly negative before rising
        assert ease_back_in(0.2) < 0


class TestEaseBackOut:
    def test_boundaries(self):
        _boundary_ok(ease_back_out)

    def test_slight_overshoot(self):
        # back-out exceeds 1 near the end
        assert ease_back_out(0.8) > 1


class TestEaseBackInOut:
    def test_boundaries(self):
        _boundary_ok(ease_back_in_out)

    def test_midpoint_is_half(self):
        assert ease_back_in_out(0.5) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# get_easing
# ---------------------------------------------------------------------------

class TestGetEasing:
    def test_known_names(self):
        for name in EASING_FUNCTIONS:
            fn = get_easing(name)
            assert callable(fn)

    def test_unknown_name_falls_back_to_linear(self):
        fn = get_easing("nonexistent_function")
        assert fn is linear

    def test_empty_string_falls_back_to_linear(self):
        fn = get_easing("")
        assert fn is linear


# ---------------------------------------------------------------------------
# interpolate
# ---------------------------------------------------------------------------

class TestInterpolate:
    def test_start_value_at_t0(self):
        assert interpolate(10, 20, 0) == pytest.approx(10.0)

    def test_end_value_at_t1(self):
        assert interpolate(10, 20, 1) == pytest.approx(20.0)

    def test_midpoint_linear(self):
        assert interpolate(0, 100, 0.5, easing="linear") == pytest.approx(50.0)

    def test_negative_range(self):
        assert interpolate(100, 0, 1) == pytest.approx(0.0)

    def test_custom_easing_applied(self):
        # With ease_in_quad: eased_t = 0.5^2 = 0.25, result = 0 + 100*0.25 = 25
        result = interpolate(0, 100, 0.5, easing="ease_in")
        assert result == pytest.approx(25.0)


# ---------------------------------------------------------------------------
# apply_squash_stretch
# ---------------------------------------------------------------------------

class TestApplySquashStretch:
    def test_zero_intensity_is_identity(self):
        scales = (1.0, 1.0)
        result = apply_squash_stretch(scales, 0.0, "vertical")
        assert result == pytest.approx((1.0, 1.0))

    def test_vertical_direction(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "vertical")
        assert h < 1.0   # compressed vertically
        assert w > 1.0   # expanded horizontally

    def test_horizontal_direction(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "horizontal")
        assert w < 1.0
        assert h > 1.0

    def test_both_direction(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "both")
        assert w < 1.0
        assert h < 1.0

    def test_unknown_direction_no_change(self):
        scales = (1.5, 2.0)
        result = apply_squash_stretch(scales, 0.5, "diagonal")
        assert result == (1.5, 2.0)


# ---------------------------------------------------------------------------
# calculate_arc_motion
# ---------------------------------------------------------------------------

class TestCalculateArcMotion:
    def test_at_t0_returns_start(self):
        pos = calculate_arc_motion((0, 0), (100, 100), 50, 0)
        assert pos == pytest.approx((0.0, 0.0))

    def test_at_t1_returns_end(self):
        pos = calculate_arc_motion((0, 0), (100, 100), 50, 1)
        assert pos == pytest.approx((100.0, 100.0))

    def test_x_is_linear(self):
        x, _ = calculate_arc_motion((0, 0), (100, 0), 0, 0.5)
        assert x == pytest.approx(50.0)

    def test_arc_peaks_at_midpoint(self):
        # With upward arc (positive height), y at midpoint should be less
        # (higher up) than linear interpolation when end == start in y
        _, y_mid = calculate_arc_motion((0, 100), (100, 100), 50, 0.5)
        # arc_offset at t=0.5 is 4*50*0.5*0.5 = 50; y = 100 + 0 - 50 = 50
        assert y_mid == pytest.approx(50.0)

    def test_zero_arc_height_is_linear(self):
        for t in [0.25, 0.5, 0.75]:
            x, y = calculate_arc_motion((0, 0), (100, 100), 0, t)
            assert x == pytest.approx(100 * t)
            assert y == pytest.approx(100 * t)
