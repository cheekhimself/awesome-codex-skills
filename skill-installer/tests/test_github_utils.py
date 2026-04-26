#!/usr/bin/env python3
"""Tests for skill-installer/scripts/github_utils.py"""

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from github_utils import github_api_contents_url, github_request


# ---------------------------------------------------------------------------
# github_api_contents_url
# ---------------------------------------------------------------------------

class TestGithubApiContentsUrl:
    def test_basic_url(self):
        url = github_api_contents_url("owner/repo", "path/to/file", "main")
        assert url == "https://api.github.com/repos/owner/repo/contents/path/to/file?ref=main"

    def test_different_ref(self):
        url = github_api_contents_url("org/project", "src/main.py", "develop")
        assert "ref=develop" in url

    def test_nested_path(self):
        url = github_api_contents_url("owner/repo", "a/b/c/d.txt", "v1.0")
        assert "/contents/a/b/c/d.txt" in url

    def test_empty_path(self):
        url = github_api_contents_url("owner/repo", "", "main")
        assert "/contents/" in url

    def test_url_starts_with_github_api(self):
        url = github_api_contents_url("owner/repo", "file.txt", "main")
        assert url.startswith("https://api.github.com/repos/")

    def test_repo_is_in_url(self):
        url = github_api_contents_url("my-org/my-repo", "file.txt", "main")
        assert "my-org/my-repo" in url


# ---------------------------------------------------------------------------
# github_request
# ---------------------------------------------------------------------------

class TestGithubRequest:
    def _make_mock_response(self, data: bytes):
        mock_resp = MagicMock()
        mock_resp.read.return_value = data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_returns_response_bytes(self):
        expected = b'{"key": "value"}'
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(expected)):
            result = github_request("https://api.github.com/test", "test-agent")
        assert result == expected

    def test_user_agent_header_set(self):
        captured = {}

        def fake_urlopen(req):
            captured["headers"] = req.headers
            return self._make_mock_response(b"ok")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            github_request("https://example.com", "my-agent")

        assert captured["headers"].get("User-agent") == "my-agent"

    def test_authorization_header_set_when_token_present(self):
        captured = {}

        def fake_urlopen(req):
            captured["headers"] = req.headers
            return self._make_mock_response(b"ok")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with patch.dict(os.environ, {"GITHUB_TOKEN": "mytoken123"}, clear=False):
                github_request("https://example.com", "agent")

        assert captured["headers"].get("Authorization") == "token mytoken123"

    def test_gh_token_env_var_used_when_no_github_token(self):
        captured = {}

        def fake_urlopen(req):
            captured["headers"] = req.headers
            return self._make_mock_response(b"ok")

        env = {"GH_TOKEN": "gh-token-456"}
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with patch.dict(os.environ, env, clear=False):
                # Ensure GITHUB_TOKEN is absent
                os.environ.pop("GITHUB_TOKEN", None)
                github_request("https://example.com", "agent")

        assert captured["headers"].get("Authorization") == "token gh-token-456"

    def test_no_authorization_header_when_no_token(self):
        captured = {}

        def fake_urlopen(req):
            captured["headers"] = req.headers
            return self._make_mock_response(b"ok")

        env_without_tokens = {k: v for k, v in os.environ.items()
                              if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with patch.dict(os.environ, env_without_tokens, clear=True):
                github_request("https://example.com", "agent")

        assert "Authorization" not in captured["headers"]

    def test_github_token_takes_precedence_over_gh_token(self):
        captured = {}

        def fake_urlopen(req):
            captured["headers"] = req.headers
            return self._make_mock_response(b"ok")

        env = {"GITHUB_TOKEN": "primary-token", "GH_TOKEN": "fallback-token"}
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with patch.dict(os.environ, env, clear=False):
                github_request("https://example.com", "agent")

        assert captured["headers"].get("Authorization") == "token primary-token"
