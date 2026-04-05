# Distribution Design: PyPI + Homebrew

**Date:** 2026-04-05  
**Status:** Approved

## Goal

Distribute `claude-prompt-refiner` publicly so any developer can install it with a single command, without requiring manual Python environment setup.

## Approach

PyPI is the source of truth for releases. A Homebrew formula in the same repo acts as a thin convenience wrapper that installs from PyPI via pipx. This keeps maintenance overhead low — version bumps flow automatically from a single publish step.

## Components

### 1. `pyproject.toml`
Package metadata and entry point definition.

- Name: `claude-prompt-refiner`
- Python requirement: `>=3.11`
- Dependencies: pulled from existing `requirements.txt` (`textual`, etc.)
- Entry point: `claude-prompt-refiner = "main:main"`
- `main.py` gets a `main()` wrapper function around `PromptRefinerApp().run()`

### 2. `.github/workflows/publish.yml`
Tag-triggered PyPI publish using OIDC trusted publishing (no stored API key).

- `v*-rc*` tags → publish to **TestPyPI** (safe dry run)
- `v*` stable tags → publish to **PyPI**
- Uses `pypa/gh-action-pypi-publish` action

### 3. `Formula/claude-prompt-refiner.rb`
Homebrew formula in the existing repo.

- `depends_on "pipx"`
- Installs via `pipx install claude-prompt-refiner`
- Install command: `brew install richeshgupta/claude-prompt-refiner/claude-prompt-refiner`

## Install Options for Users

```bash
# Via Homebrew (Mac/Linux)
brew install richeshgupta/claude-prompt-refiner/claude-prompt-refiner

# Via pipx (Python-native, cross-platform)
pipx install claude-prompt-refiner

# Via pip
pip install claude-prompt-refiner
```

## Release Flow

```
git tag v1.0.0 && git push --tags
  → GitHub Actions: python -m build → pypa/gh-action-pypi-publish → PyPI
  → brew install pulls latest from PyPI automatically
```

## Testing

| Test | Trigger | Tool |
|---|---|---|
| Package builds cleanly | Every PR | `python -m build` in CI |
| Entry point works | Every PR | Install in venv, assert `claude-prompt-refiner --help` exits 0 |
| TestPyPI dry run | `v*-rc*` tag | Full publish pipeline to TestPyPI |
| Formula lint | Every PR | `brew audit --formula Formula/claude-prompt-refiner.rb` |

## Tag Convention

```bash
git tag v1.0.0-rc1   # → TestPyPI (validate pipeline)
git tag v1.0.0       # → PyPI (real release)
```

## Files Added/Modified

| File | Change |
|---|---|
| `pyproject.toml` | New |
| `main.py` | Add `main()` wrapper |
| `.github/workflows/publish.yml` | New |
| `Formula/claude-prompt-refiner.rb` | New |
| `docs/plans/2026-04-05-homebrew-pypi-distribution-design.md` | New (this file) |
