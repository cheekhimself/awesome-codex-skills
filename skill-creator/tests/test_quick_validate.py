#!/usr/bin/env python3
"""Tests for skill-creator/scripts/quick_validate.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from quick_validate import MAX_SKILL_NAME_LENGTH, validate_skill


def _write_skill(tmp_path, content):
    """Helper: write a SKILL.md with given content and return the dir path."""
    (tmp_path / "SKILL.md").write_text(content)
    return tmp_path


def _valid_frontmatter(**kwargs):
    """Build minimal valid frontmatter with optional overrides."""
    data = {"name": "my-skill", "description": "A test skill"}
    data.update(kwargs)
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, str):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {v!r}")
    lines.append("---")
    lines.append("")
    lines.append("# My Skill")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Missing SKILL.md
# ---------------------------------------------------------------------------

class TestMissingSkillMd:
    def test_missing_file_returns_false(self, tmp_path):
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "not found" in msg.lower() or "SKILL.md" in msg


# ---------------------------------------------------------------------------
# Frontmatter format
# ---------------------------------------------------------------------------

class TestFrontmatterFormat:
    def test_no_yaml_frontmatter_returns_false(self, tmp_path):
        _write_skill(tmp_path, "# Just a heading\nNo frontmatter here.\n")
        valid, msg = validate_skill(tmp_path)
        assert valid is False

    def test_unterminated_frontmatter_returns_false(self, tmp_path):
        _write_skill(tmp_path, "---\nname: my-skill\ndescription: test\n")
        valid, msg = validate_skill(tmp_path)
        assert valid is False

    def test_non_dict_frontmatter_returns_false(self, tmp_path):
        _write_skill(tmp_path, "---\n- item1\n- item2\n---\n")
        valid, msg = validate_skill(tmp_path)
        assert valid is False


# ---------------------------------------------------------------------------
# Valid skill
# ---------------------------------------------------------------------------

class TestValidSkill:
    def test_minimal_valid_skill(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter())
        valid, msg = validate_skill(tmp_path)
        assert valid is True

    def test_valid_with_optional_license(self, tmp_path):
        content = "---\nname: my-skill\ndescription: A test skill\nlicense: MIT\n---\n"
        _write_skill(tmp_path, content)
        valid, _ = validate_skill(tmp_path)
        assert valid is True

    def test_valid_with_allowed_tools(self, tmp_path):
        content = (
            "---\n"
            "name: my-skill\n"
            "description: A test skill\n"
            "allowed-tools:\n"
            "  - Bash\n"
            "---\n"
        )
        _write_skill(tmp_path, content)
        valid, _ = validate_skill(tmp_path)
        assert valid is True

    def test_valid_with_metadata(self, tmp_path):
        content = (
            "---\n"
            "name: my-skill\n"
            "description: A test skill\n"
            "metadata:\n"
            "  author: tester\n"
            "---\n"
        )
        _write_skill(tmp_path, content)
        valid, _ = validate_skill(tmp_path)
        assert valid is True


# ---------------------------------------------------------------------------
# Unexpected keys
# ---------------------------------------------------------------------------

class TestUnexpectedKeys:
    def test_unexpected_key_returns_false(self, tmp_path):
        content = "---\nname: my-skill\ndescription: A test\nunknown-key: value\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "unexpected" in msg.lower() or "unknown-key" in msg

    def test_error_message_lists_allowed_properties(self, tmp_path):
        content = "---\nname: my-skill\ndescription: A test\nbad: val\n---\n"
        _write_skill(tmp_path, content)
        _, msg = validate_skill(tmp_path)
        assert "name" in msg and "description" in msg


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingRequiredFields:
    def test_missing_name_returns_false(self, tmp_path):
        content = "---\ndescription: A test skill\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "name" in msg.lower()

    def test_missing_description_returns_false(self, tmp_path):
        content = "---\nname: my-skill\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "description" in msg.lower()


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------

class TestNameValidation:
    def test_name_must_be_lowercase_hyphen(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="MySkill"))
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "hyphen-case" in msg.lower() or "lowercase" in msg.lower()

    def test_name_with_spaces_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="my skill"))
        valid, _ = validate_skill(tmp_path)
        assert valid is False

    def test_name_with_uppercase_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="My-Skill"))
        valid, _ = validate_skill(tmp_path)
        assert valid is False

    def test_name_starting_with_hyphen_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="-my-skill"))
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "hyphen" in msg.lower()

    def test_name_ending_with_hyphen_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="my-skill-"))
        valid, msg = validate_skill(tmp_path)
        assert valid is False

    def test_name_with_consecutive_hyphens_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="my--skill"))
        valid, msg = validate_skill(tmp_path)
        assert valid is False

    def test_name_too_long_is_invalid(self, tmp_path):
        long_name = "a" * (MAX_SKILL_NAME_LENGTH + 1)
        _write_skill(tmp_path, _valid_frontmatter(name=long_name))
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "too long" in msg.lower() or "maximum" in msg.lower()

    def test_name_exactly_max_length_is_valid(self, tmp_path):
        exact_name = "a" * MAX_SKILL_NAME_LENGTH
        _write_skill(tmp_path, _valid_frontmatter(name=exact_name))
        valid, _ = validate_skill(tmp_path)
        assert valid is True

    def test_name_with_digits_is_valid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(name="skill-123"))
        valid, _ = validate_skill(tmp_path)
        assert valid is True

    def test_name_must_be_string(self, tmp_path):
        content = "---\nname: 12345\ndescription: A test skill\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "string" in msg.lower()


# ---------------------------------------------------------------------------
# Description validation
# ---------------------------------------------------------------------------

class TestDescriptionValidation:
    def test_description_with_angle_brackets_is_invalid(self, tmp_path):
        _write_skill(tmp_path, _valid_frontmatter(description="<script>alert(1)</script>"))
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "angle" in msg.lower() or "<" in msg or ">" in msg

    def test_description_too_long_is_invalid(self, tmp_path):
        long_desc = "a" * 1025
        _write_skill(tmp_path, _valid_frontmatter(description=long_desc))
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "too long" in msg.lower() or "maximum" in msg.lower()

    def test_description_exactly_max_length_is_valid(self, tmp_path):
        exact_desc = "a" * 1024
        _write_skill(tmp_path, _valid_frontmatter(description=exact_desc))
        valid, _ = validate_skill(tmp_path)
        assert valid is True

    def test_description_must_be_string(self, tmp_path):
        content = "---\nname: my-skill\ndescription: 42\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "string" in msg.lower()

    def test_invalid_yaml_in_frontmatter(self, tmp_path):
        content = "---\nname: my-skill\ndescription: test\nbad: [\n---\n"
        _write_skill(tmp_path, content)
        valid, msg = validate_skill(tmp_path)
        assert valid is False
        assert "yaml" in msg.lower() or "invalid" in msg.lower()
