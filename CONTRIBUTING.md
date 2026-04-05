# Contributing to claude-prompt-refiner

## Prerequisites

- Python 3.11+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated

## Setup

```bash
git clone https://github.com/richeshgupta/claude-prompt-refiner-adv.git
cd claude-prompt-refiner-adv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # or: pip install -r requirements.txt
python main.py            # verify the setup works
```

## Running Tests

```bash
pytest tests/
```

## Code Style

No linter is enforced. Follow the patterns already present in the codebase:

- Do not add type annotations to code you are not otherwise changing.
- Do not add docstrings to simple functions.
- Keep changes consistent with the surrounding code.

## Making Changes

1. Branch from `master`.
2. Make your changes and ensure all CI checks pass.
3. Open a pull request — one approval from @richeshgupta is required before merging.

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix  | When to use                          |
|---------|--------------------------------------|
| `feat:` | New feature                          |
| `fix:`  | Bug fix                              |
| `ci:`   | CI/CD changes                        |
| `docs:` | Documentation only                   |
| `chore:`| Maintenance, deps, tooling           |

Example: `feat: add retry logic for API timeouts`

## Reporting Bugs

Open a GitHub issue with:

- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS

## Feature Requests

Open a GitHub issue describing the use case and why it would be useful.
