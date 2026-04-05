# Prompt Refiner — Design Document

**Date:** 2026-04-05  
**Status:** Approved

## Problem

No existing tool auto-rewrites prompts at input time. Developers write raw prompts and have no feedback loop for improving them systematically.

## Solution

A developer-native interactive TUI that:
1. Takes a raw prompt as input
2. Sends it to Claude (via Claude Code subscription) for refinement
3. Applies proven prompt engineering techniques automatically
4. Presents the refined prompt with annotations explaining each change
5. Lets the user Accept / Reject / Refine-with-comments

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚡ Prompt Refiner   Model: [claude-sonnet-4-6 ▾]   q:quit  ?:help  │
├────────────────────────┬────────────────────────────────────────────┤
│  YOUR PROMPT           │  REFINED PROMPT                            │
│  <TextArea>            │  <RichLog - streamed>                      │
├────────────────────────┴────────────────────────────────────────────┤
│  ANNOTATIONS                                                        │
│  ► Role prompting added — code generation task detected             │
├─────────────────────────────────────────────────────────────────────┤
│  Ctrl+Enter: Refine  │  y: Accept  │  n: Reject  │  e: Edit+Refine  │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| TUI | `textual` | Best Python TUI library, reactive, built-in widgets |
| Claude calls | `subprocess → claude -p` | Works with Claude Code subscription, zero extra cost |
| Clipboard | `pyperclip` | Cross-platform |
| Python | 3.11+ | Textual requirement |

## Auth

Zero config for Claude Code subscribers. Uses existing `claude` binary authentication.
- Error if `claude` not in PATH → "Install Claude Code"
- Error if not logged in → "Run `claude login`"

## Prompt Techniques Applied

| Detected Task | Techniques Injected |
|---|---|
| Code generation | Role prompt (expert engineer), CoT, output format (code block) |
| Debugging | Role prompt, constraint injection, step-by-step |
| Explanation | Audience injection, XML structure |
| General | XML structure, explicit output format, CoT |

## Keybindings

| Key | Action |
|---|---|
| `Ctrl+Enter` | Trigger refinement |
| `y` | Accept → copy to clipboard |
| `n` | Reject → clear output, back to input |
| `e` | Refine with comments → opens comment dialog |
| `Tab` | Cycle model (haiku → sonnet → opus) |
| `q` | Quit |
| `?` | Toggle help overlay |

## Models

- `claude-haiku-4-5` (fast, cheap)
- `claude-sonnet-4-6` (default, balanced)
- `claude-opus-4-6` (most capable)
