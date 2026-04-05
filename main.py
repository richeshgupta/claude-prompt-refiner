# main.py
"""Entry point for the Prompt Refiner TUI."""

from __future__ import annotations

import sys
from claude import check_claude_available
from app import PromptRefinerApp


def main() -> None:
    if not check_claude_available():
        print(
            "✗ Error: claude CLI not found.\n"
            "  Install Claude Code: https://claude.ai/code\n"
            "  Then run: claude login"
        )
        sys.exit(1)

    app = PromptRefinerApp()
    app.run()


if __name__ == "__main__":
    main()
