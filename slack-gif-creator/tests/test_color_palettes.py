#!/usr/bin/env python3
"""Tests for slack-gif-creator/core/color_palettes.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.color_palettes import (
    EMOJI_PALETTES,
    IMPACT_COLORS,
    PALETTES,
    blend_colors,
    create_gradient_colors,
    darken_color,
    get_complementary_color,
    get_emoji_palette,
    get_impact_color,
    get_palette,
    get_text_color_for_background,
    lighten_color,
)


# ---------------------------------------------------------------------------
# get_palette
# ---------------------------------------------------------------------------

class TestGetPalette:
    def test_known_palettes_returned(self):
        for name in PALETTES:
            palette = get_palette(name)
            assert isinstance(palette, dict)
            assert "primary" in palette

    def test_case_insensitive(self):
        assert get_palette("Vibrant") == get_palette("vibrant")
        assert get_palette("DARK") == get_palette("dark")

    def test_unknown_name_returns_vibrant(self):
        palette = get_palette("does_not_exist")
        from core.color_palettes import VIBRANT
        assert palette == VIBRANT

    def test_each_palette_has_required_keys(self):
        required = {"primary", "secondary", "accent", "success", "background", "text", "text_light"}
        for name, palette in PALETTES.items():
            missing = required - set(palette.keys())
            assert not missing, f"Palette '{name}' is missing keys: {missing}"


# ---------------------------------------------------------------------------
# get_text_color_for_background
# ---------------------------------------------------------------------------

class TestGetTextColorForBackground:
    def test_white_background_returns_black(self):
        assert get_text_color_for_background((255, 255, 255)) == (0, 0, 0)

    def test_black_background_returns_white(self):
        assert get_text_color_for_background((0, 0, 0)) == (255, 255, 255)

    def test_light_gray_returns_black(self):
        assert get_text_color_for_background((200, 200, 200)) == (0, 0, 0)

    def test_dark_blue_returns_white(self):
        assert get_text_color_for_background((0, 0, 100)) == (255, 255, 255)

    def test_medium_gray_boundary(self):
        # luminance ≈ 0.5, both results are valid; just confirm it returns one of the two
        color = get_text_color_for_background((128, 128, 128))
        assert color in ((0, 0, 0), (255, 255, 255))


# ---------------------------------------------------------------------------
# get_complementary_color
# ---------------------------------------------------------------------------

class TestGetComplementaryColor:
    def test_returns_tuple_of_three_ints(self):
        result = get_complementary_color((255, 0, 0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(v, int) for v in result)

    def test_values_in_valid_range(self):
        for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 64, 200)]:
            r, g, b = get_complementary_color(color)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_complement_of_complement_approx_original(self):
        original = (200, 100, 50)
        comp = get_complementary_color(original)
        comp2 = get_complementary_color(comp)
        # Due to integer rounding, allow ±2 per channel
        for o, c in zip(original, comp2):
            assert abs(o - c) <= 2

    def test_red_complementary_is_cyan_ish(self):
        # Pure red (255,0,0) → hue 0 → complement hue 0.5 → (0,255,255) cyan
        r, g, b = get_complementary_color((255, 0, 0))
        assert r == pytest.approx(0, abs=2)
        assert g == pytest.approx(255, abs=2)
        assert b == pytest.approx(255, abs=2)


# ---------------------------------------------------------------------------
# lighten_color
# ---------------------------------------------------------------------------

class TestLightenColor:
    def test_zero_amount_is_identity(self):
        color = (100, 150, 200)
        assert lighten_color(color, 0.0) == color

    def test_full_amount_returns_white(self):
        assert lighten_color((0, 0, 0), 1.0) == (255, 255, 255)

    def test_lightened_values_increase(self):
        original = (100, 100, 100)
        lightened = lighten_color(original, 0.5)
        for o, l in zip(original, lightened):
            assert l >= o

    def test_values_capped_at_255(self):
        r, g, b = lighten_color((255, 255, 255), 1.0)
        assert r <= 255 and g <= 255 and b <= 255


# ---------------------------------------------------------------------------
# darken_color
# ---------------------------------------------------------------------------

class TestDarkenColor:
    def test_zero_amount_is_identity(self):
        color = (100, 150, 200)
        assert darken_color(color, 0.0) == color

    def test_full_amount_returns_black(self):
        assert darken_color((255, 255, 255), 1.0) == (0, 0, 0)

    def test_darkened_values_decrease(self):
        original = (200, 150, 100)
        darkened = darken_color(original, 0.5)
        for o, d in zip(original, darkened):
            assert d <= o

    def test_values_floored_at_0(self):
        r, g, b = darken_color((0, 0, 0), 1.0)
        assert r >= 0 and g >= 0 and b >= 0


# ---------------------------------------------------------------------------
# blend_colors
# ---------------------------------------------------------------------------

class TestBlendColors:
    def test_ratio_zero_returns_color1(self):
        assert blend_colors((255, 0, 0), (0, 255, 0), 0.0) == (255, 0, 0)

    def test_ratio_one_returns_color2(self):
        assert blend_colors((255, 0, 0), (0, 255, 0), 1.0) == (0, 255, 0)

    def test_midpoint_blend(self):
        r, g, b = blend_colors((0, 0, 0), (100, 100, 100), 0.5)
        assert r == 50 and g == 50 and b == 50

    def test_result_in_valid_range(self):
        r, g, b = blend_colors((200, 100, 50), (50, 200, 150), 0.4)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


# ---------------------------------------------------------------------------
# create_gradient_colors
# ---------------------------------------------------------------------------

class TestCreateGradientColors:
    def test_single_step_returns_start_color(self):
        result = create_gradient_colors((255, 0, 0), (0, 0, 255), 1)
        assert len(result) == 1
        assert result[0] == (255, 0, 0)

    def test_two_steps_returns_start_and_end(self):
        result = create_gradient_colors((0, 0, 0), (255, 255, 255), 2)
        assert len(result) == 2
        assert result[0] == (0, 0, 0)
        assert result[1] == (255, 255, 255)

    def test_length_matches_steps(self):
        for steps in [3, 5, 10]:
            result = create_gradient_colors((0, 0, 0), (255, 255, 255), steps)
            assert len(result) == steps

    def test_monotone_gradient(self):
        result = create_gradient_colors((0, 0, 0), (255, 255, 255), 5)
        # Each step should be ≥ previous in all channels
        for i in range(1, len(result)):
            for prev, curr in zip(result[i - 1], result[i]):
                assert curr >= prev

    def test_all_tuples_in_valid_range(self):
        result = create_gradient_colors((10, 20, 30), (200, 210, 220), 7)
        for color in result:
            assert len(color) == 3
            for v in color:
                assert 0 <= v <= 255


# ---------------------------------------------------------------------------
# get_impact_color
# ---------------------------------------------------------------------------

class TestGetImpactColor:
    def test_known_types_returned(self):
        for name in IMPACT_COLORS:
            color = get_impact_color(name)
            assert len(color) == 3

    def test_unknown_type_returns_flash(self):
        assert get_impact_color("unknown_effect") == IMPACT_COLORS["flash"]

    def test_default_is_flash(self):
        assert get_impact_color() == IMPACT_COLORS["flash"]


# ---------------------------------------------------------------------------
# get_emoji_palette
# ---------------------------------------------------------------------------

class TestGetEmojiPalette:
    def test_known_palettes_returned(self):
        for name in EMOJI_PALETTES:
            palette = get_emoji_palette(name)
            assert isinstance(palette, list)
            assert len(palette) > 0

    def test_unknown_name_returns_simple(self):
        assert get_emoji_palette("nonexistent") == EMOJI_PALETTES["simple"]

    def test_all_colors_are_valid_rgb(self):
        for name in EMOJI_PALETTES:
            for color in get_emoji_palette(name):
                assert len(color) == 3
                for v in color:
                    assert 0 <= v <= 255
