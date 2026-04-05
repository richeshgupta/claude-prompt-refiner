# tests/test_claude.py
import pytest
from unittest.mock import patch, MagicMock
from claude import check_claude_available, run_claude, ClaudeNotFoundError, ClaudeError

def test_check_claude_available_when_present():
    with patch("shutil.which", return_value="/usr/bin/claude"):
        assert check_claude_available() is True

def test_check_claude_available_when_absent():
    with patch("shutil.which", return_value=None):
        assert check_claude_available() is False

def test_run_claude_raises_if_not_found():
    with patch("shutil.which", return_value=None):
        with pytest.raises(ClaudeNotFoundError):
            run_claude("hello", "claude-sonnet-4-6")

def test_run_claude_returns_stdout_on_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "refined prompt here"
    mock_result.stderr = ""
    with patch("shutil.which", return_value="/usr/bin/claude"):
        with patch("subprocess.run", return_value=mock_result):
            result = run_claude("hello", "claude-sonnet-4-6")
            assert result == "refined prompt here"

def test_run_claude_raises_on_nonzero_exit():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "authentication error"
    with patch("shutil.which", return_value="/usr/bin/claude"):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ClaudeError, match="authentication error"):
                run_claude("hello", "claude-sonnet-4-6")
