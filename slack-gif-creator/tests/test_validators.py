#!/usr/bin/env python3
"""Tests for slack-gif-creator/core/validators.py"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.validators import (
    check_slack_size,
    get_optimization_suggestions,
    validate_dimensions,
)


# ---------------------------------------------------------------------------
# check_slack_size
# ---------------------------------------------------------------------------

class TestCheckSlackSize:
    def test_nonexistent_file_returns_false(self):
        passes, info = check_slack_size("/nonexistent/path/file.gif")
        assert passes is False
        assert "error" in info

    def test_small_emoji_gif_passes(self, tmp_path):
        gif = tmp_path / "small.gif"
        gif.write_bytes(b"x" * 1024)  # 1 KB  < 64 KB limit
        passes, info = check_slack_size(gif, is_emoji=True)
        assert passes is True
        assert info["type"] == "emoji"
        assert info["limit_kb"] == 64

    def test_large_emoji_gif_fails(self, tmp_path):
        gif = tmp_path / "big.gif"
        gif.write_bytes(b"x" * (65 * 1024))  # 65 KB > 64 KB limit
        passes, info = check_slack_size(gif, is_emoji=True)
        assert passes is False
        assert info["size_kb"] > 64

    def test_message_gif_limit_is_2mb(self, tmp_path):
        gif = tmp_path / "msg.gif"
        gif.write_bytes(b"x" * (1024 * 1024))  # 1 MB < 2 MB limit
        passes, info = check_slack_size(gif, is_emoji=False)
        assert passes is True
        assert info["limit_kb"] == 2048

    def test_info_dict_keys_present(self, tmp_path):
        gif = tmp_path / "any.gif"
        gif.write_bytes(b"x" * 100)
        _, info = check_slack_size(gif)
        assert {"size_bytes", "size_kb", "size_mb", "limit_kb", "limit_mb", "passes", "type"}.issubset(info.keys())

    def test_accepts_path_object(self, tmp_path):
        gif = tmp_path / "path_obj.gif"
        gif.write_bytes(b"x" * 512)
        passes, _ = check_slack_size(Path(gif))
        assert passes is True


# ---------------------------------------------------------------------------
# validate_dimensions
# ---------------------------------------------------------------------------

class TestValidateDimensions:
    # --- emoji mode ---

    def test_optimal_emoji_128x128(self):
        passes, info = validate_dimensions(128, 128, is_emoji=True)
        assert passes is True
        assert info["optimal"] is True

    def test_acceptable_emoji_64x64(self):
        passes, info = validate_dimensions(64, 64, is_emoji=True)
        assert passes is True
        assert info["acceptable"] is True

    def test_non_square_emoji_fails(self):
        passes, info = validate_dimensions(128, 64, is_emoji=True)
        assert passes is False
        assert info["is_square"] is False

    def test_too_small_emoji_fails(self):
        passes, _ = validate_dimensions(32, 32, is_emoji=True)
        assert passes is False

    def test_too_large_emoji_fails(self):
        passes, _ = validate_dimensions(256, 256, is_emoji=True)
        assert passes is False

    # --- message mode ---

    def test_square_reasonable_message_gif_passes(self):
        passes, info = validate_dimensions(512, 512, is_emoji=False)
        assert passes is True
        assert info["type"] == "message"

    def test_wide_message_gif_passes_with_warning(self):
        # 640×320 is 2:1 — exactly at boundary, should pass
        passes, _ = validate_dimensions(640, 320, is_emoji=False)
        assert passes is True

    def test_very_wide_message_gif_still_passes_if_good_size(self):
        # aspect ratio > 2:1 but reasonable size → still passes with warning
        passes, _ = validate_dimensions(640, 320, is_emoji=False)
        assert passes is True

    def test_tiny_message_gif_passes_with_warning(self):
        # small size but square — passes with warning
        passes, _ = validate_dimensions(100, 100, is_emoji=False)
        assert passes is True

    def test_info_contains_aspect_ratio_for_message(self):
        _, info = validate_dimensions(400, 200, is_emoji=False)
        assert "aspect_ratio" in info

    def test_type_field_set_correctly(self):
        _, emoji_info = validate_dimensions(128, 128, is_emoji=True)
        assert emoji_info["type"] == "emoji"
        _, msg_info = validate_dimensions(400, 400, is_emoji=False)
        assert msg_info["type"] == "message"


# ---------------------------------------------------------------------------
# get_optimization_suggestions
# ---------------------------------------------------------------------------

class TestGetOptimizationSuggestions:
    def _passing_results(self):
        return {
            "passes": True,
            "size": {"passes": True, "size_kb": 10, "limit_kb": 64, "type": "emoji"},
            "dimensions": {"optimal": True, "acceptable": True, "type": "emoji"},
        }

    def _failing_emoji_results(self, size_kb=80):
        return {
            "passes": False,
            "size": {
                "passes": False,
                "size_kb": size_kb,
                "limit_kb": 64,
                "type": "emoji",
            },
            "dimensions": {"optimal": True, "acceptable": True, "type": "emoji"},
        }

    def test_no_suggestions_when_passing(self):
        suggestions = get_optimization_suggestions(self._passing_results())
        assert suggestions == []

    def test_suggestions_returned_when_failing(self):
        suggestions = get_optimization_suggestions(self._failing_emoji_results())
        assert len(suggestions) > 0

    def test_suggestions_are_strings(self):
        suggestions = get_optimization_suggestions(self._failing_emoji_results())
        for s in suggestions:
            assert isinstance(s, str)

    def test_emoji_size_suggestions_mention_frames(self):
        suggestions = get_optimization_suggestions(self._failing_emoji_results())
        combined = "\n".join(suggestions)
        assert "frame" in combined.lower() or "color" in combined.lower()

    def test_message_size_suggestions(self):
        results = {
            "passes": False,
            "size": {
                "passes": False,
                "size_kb": 3000,
                "limit_kb": 2048,
                "type": "message",
            },
            "dimensions": {"aspect_ratio": 1.0, "type": "message"},
        }
        suggestions = get_optimization_suggestions(results)
        assert len(suggestions) > 0

    def test_dimension_suggestions_for_non_optimal_emoji(self):
        results = {
            "passes": False,
            "size": {"passes": True, "size_kb": 10, "limit_kb": 64, "type": "emoji"},
            "dimensions": {"optimal": False, "acceptable": False, "type": "emoji"},
        }
        suggestions = get_optimization_suggestions(results)
        combined = "\n".join(suggestions)
        assert "128" in combined or "square" in combined.lower()

    def test_empty_results_dict_returns_empty_list(self):
        suggestions = get_optimization_suggestions({})
        assert suggestions == []
