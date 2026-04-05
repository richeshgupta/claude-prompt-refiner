# claude.py
"""Subprocess wrapper around the `claude` CLI."""

from __future__ import annotations

import shutil
import subprocess

MODELS = [
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
]

DEFAULT_MODEL = "claude-sonnet-4-6"


class ClaudeNotFoundError(Exception):
    """Raised when the claude CLI binary is not found in PATH."""


class ClaudeError(Exception):
    """Raised when claude exits with a non-zero return code."""


def check_claude_available() -> bool:
    """Return True if the claude binary is in PATH."""
    return shutil.which("claude") is not None


def run_claude(prompt: str, model: str, timeout: int = 120) -> str:
    """Run `claude -p <prompt> --model <model>` and return stdout."""
    if not check_claude_available():
        raise ClaudeNotFoundError(
            "claude CLI not found. Install Claude Code: https://claude.ai/code"
        )

    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or f"Exit code {result.returncode}"
        raise ClaudeError(error_msg)

    return result.stdout.strip()


def next_model(current: str) -> str:
    """Return the next model in the rotation."""
    try:
        idx = MODELS.index(current)
    except ValueError:
        return DEFAULT_MODEL
    return MODELS[(idx + 1) % len(MODELS)]
