# Prompt Refiner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a developer TUI that refines prompts using Claude Code subscription via subprocess.

**Architecture:** Textual TUI with 3 panels (input/output/annotations). RefinerEngine builds a structured prompt sent to `claude -p` subprocess. Response is JSON with `refined_prompt` + `annotations`.

**Tech Stack:** Python 3.11+, textual, pyperclip, subprocess (claude CLI)

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

**Step 1: Write requirements.txt**

```
textual>=0.60.0
pyperclip>=1.8.0
```

**Step 2: Install dependencies**

```bash
cd /home/richesh/Desktop/expts/claude-prompt-refiner-adv
pip install textual pyperclip
```

Expected: packages install without error.

**Step 3: Verify claude CLI available**

```bash
which claude && claude --version
```

Expected: prints path and version. If not found, user needs to install Claude Code.

**Step 4: Create tests/__init__.py**

```bash
touch tests/__init__.py
```

**Step 5: Commit**

```bash
git init
git add requirements.txt tests/__init__.py docs/
git commit -m "chore: project setup and design docs"
```

---

### Task 2: techniques.py — Prompt Technique Definitions

**Files:**
- Create: `techniques.py`
- Create: `tests/test_techniques.py`

**Step 1: Write failing test**

```python
# tests/test_techniques.py
from techniques import detect_task_type, get_techniques_for_task

def test_detect_code_task():
    assert detect_task_type("write a python function to sort a list") == "code"

def test_detect_debug_task():
    assert detect_task_type("fix this bug in my code") == "debug"

def test_detect_explanation_task():
    assert detect_task_type("explain how neural networks work") == "explanation"

def test_detect_general_task():
    assert detect_task_type("what is the best way to structure a team") == "general"

def test_techniques_for_code():
    techniques = get_techniques_for_task("code")
    names = [t["name"] for t in techniques]
    assert "Role prompting" in names
    assert "Chain-of-thought" in names

def test_techniques_for_general():
    techniques = get_techniques_for_task("general")
    names = [t["name"] for t in techniques]
    assert "XML structuring" in names
```

**Step 2: Run test to verify it fails**

```bash
cd /home/richesh/Desktop/expts/claude-prompt-refiner-adv
python -m pytest tests/test_techniques.py -v
```

Expected: ImportError or ModuleNotFoundError.

**Step 3: Implement techniques.py**

```python
# techniques.py
"""Prompt engineering technique definitions and task detection."""

from __future__ import annotations

# Keywords used to detect task type from the raw prompt
_CODE_KEYWORDS = {
    "write", "implement", "code", "function", "class", "script",
    "program", "algorithm", "method", "api", "endpoint", "build",
    "create a", "develop", "refactor", "unit test", "def ", "sql",
}
_DEBUG_KEYWORDS = {
    "fix", "bug", "error", "debug", "broken", "fails", "crash",
    "exception", "traceback", "not working", "issue", "problem",
}
_EXPLAIN_KEYWORDS = {
    "explain", "what is", "how does", "why does", "describe",
    "summarize", "what are", "define", "clarify", "tell me about",
}

# Technique catalogue — each entry describes one technique
TECHNIQUES: dict[str, dict] = {
    "role_prompting": {
        "name": "Role prompting",
        "instruction": (
            "Prepend a role statement: 'You are an expert [relevant domain] professional.'"
        ),
        "applies_to": ["code", "debug", "explanation", "general"],
    },
    "chain_of_thought": {
        "name": "Chain-of-thought",
        "instruction": (
            "Append 'Think step by step before answering.' to encourage reasoning."
        ),
        "applies_to": ["code", "debug", "general"],
    },
    "xml_structuring": {
        "name": "XML structuring",
        "instruction": (
            "Wrap distinct sections in XML tags: "
            "<instructions>, <context>, <constraints>, <output_format>."
        ),
        "applies_to": ["code", "debug", "explanation", "general"],
    },
    "output_format": {
        "name": "Output format",
        "instruction": (
            "Add an explicit <output_format> section specifying "
            "the expected structure, length, and style."
        ),
        "applies_to": ["code", "explanation", "general"],
    },
    "constraint_injection": {
        "name": "Constraint injection",
        "instruction": (
            "Add negative constraints relevant to common failure modes "
            "(e.g., 'Do not change unrelated code', 'Do not hallucinate imports')."
        ),
        "applies_to": ["debug", "code"],
    },
    "audience_injection": {
        "name": "Audience injection",
        "instruction": (
            "Specify the audience level: "
            "'Explain this to a senior software engineer who is unfamiliar with this domain.'"
        ),
        "applies_to": ["explanation"],
    },
}

# Which techniques apply per task type (ordered by priority)
_TASK_TECHNIQUE_MAP: dict[str, list[str]] = {
    "code": [
        "role_prompting",
        "chain_of_thought",
        "xml_structuring",
        "output_format",
        "constraint_injection",
    ],
    "debug": [
        "role_prompting",
        "constraint_injection",
        "chain_of_thought",
        "xml_structuring",
    ],
    "explanation": [
        "role_prompting",
        "audience_injection",
        "xml_structuring",
        "output_format",
    ],
    "general": [
        "role_prompting",
        "xml_structuring",
        "output_format",
        "chain_of_thought",
    ],
}


def detect_task_type(prompt: str) -> str:
    """Detect task type from the raw prompt text.

    Returns one of: 'code', 'debug', 'explanation', 'general'.
    """
    lower = prompt.lower()
    # Debug takes priority — it often contains code keywords too
    if any(kw in lower for kw in _DEBUG_KEYWORDS):
        return "debug"
    if any(kw in lower for kw in _CODE_KEYWORDS):
        return "code"
    if any(kw in lower for kw in _EXPLAIN_KEYWORDS):
        return "explanation"
    return "general"


def get_techniques_for_task(task_type: str) -> list[dict]:
    """Return ordered list of technique dicts for the given task type."""
    keys = _TASK_TECHNIQUE_MAP.get(task_type, _TASK_TECHNIQUE_MAP["general"])
    return [TECHNIQUES[k] for k in keys]
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_techniques.py -v
```

Expected: all 6 tests PASS.

**Step 5: Commit**

```bash
git add techniques.py tests/test_techniques.py
git commit -m "feat: add task detection and technique catalogue"
```

---

### Task 3: engine.py — RefinerEngine

**Files:**
- Create: `engine.py`
- Create: `tests/test_engine.py`

**Step 1: Write failing tests**

```python
# tests/test_engine.py
from engine import RefinerEngine

def test_build_refiner_prompt_contains_original():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("write a sort function", comment=None)
    assert "write a sort function" in prompt

def test_build_refiner_prompt_contains_json_instruction():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("explain recursion", comment=None)
    assert "JSON" in prompt
    assert "refined_prompt" in prompt
    assert "annotations" in prompt

def test_build_refiner_prompt_with_comment():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("write code", comment="make it shorter")
    assert "make it shorter" in prompt

def test_parse_response_valid_json():
    engine = RefinerEngine()
    raw = '{"refined_prompt": "You are an expert. Write code.", "annotations": [{"technique": "Role prompting", "reason": "code task"}]}'
    result = engine.parse_response(raw)
    assert result["refined_prompt"] == "You are an expert. Write code."
    assert len(result["annotations"]) == 1

def test_parse_response_extracts_json_from_text():
    engine = RefinerEngine()
    raw = 'Here is the refined prompt:\n\n```json\n{"refined_prompt": "test", "annotations": []}\n```'
    result = engine.parse_response(raw)
    assert result["refined_prompt"] == "test"

def test_parse_response_returns_fallback_on_failure():
    engine = RefinerEngine()
    result = engine.parse_response("this is not json at all")
    assert "refined_prompt" in result
    assert "annotations" in result
```

**Step 2: Run to verify they fail**

```bash
python -m pytest tests/test_engine.py -v
```

Expected: ImportError — engine module not found.

**Step 3: Implement engine.py**

```python
# engine.py
"""RefinerEngine: builds prompts for Claude and parses its JSON response."""

from __future__ import annotations

import json
import re

from techniques import detect_task_type, get_techniques_for_task

_REFINER_SYSTEM = """\
You are an expert prompt engineer. Your task is to improve the user's prompt \
by applying proven prompt engineering techniques.

You must return ONLY a valid JSON object — no markdown fences, no explanation, \
no text before or after the JSON. The JSON must have exactly this shape:

{{
  "refined_prompt": "<the improved prompt as a plain string>",
  "annotations": [
    {{"technique": "<technique name>", "reason": "<why this technique was applied>"}}
  ]
}}

Techniques to consider (apply only those that genuinely improve the prompt):
{technique_list}

Rules:
- Preserve the user's intent exactly — only improve structure and clarity
- Do not add fictional context or assumptions
- Keep the refined prompt concise — do not pad unnecessarily
- If the prompt is already excellent, still apply at least one technique\
"""

_USER_TEMPLATE = """\
Refine this prompt:

{prompt}{comment_section}
"""

_COMMENT_SECTION = "\n\nAdditional instructions from user: {comment}"


class RefinerEngine:
    """Builds the refiner prompt and parses Claude's JSON response."""

    def build_refiner_prompt(self, raw_prompt: str, comment: str | None) -> str:
        """Return the full prompt to send to Claude for refinement."""
        task_type = detect_task_type(raw_prompt)
        techniques = get_techniques_for_task(task_type)
        technique_list = "\n".join(
            f"- {t['name']}: {t['instruction']}" for t in techniques
        )
        system = _REFINER_SYSTEM.format(technique_list=technique_list)
        comment_section = (
            _COMMENT_SECTION.format(comment=comment) if comment else ""
        )
        user_msg = _USER_TEMPLATE.format(
            prompt=raw_prompt, comment_section=comment_section
        )
        # Combine system + user into one prompt (claude -p has no --system flag)
        return f"{system}\n\n---\n\n{user_msg}"

    def parse_response(self, raw: str) -> dict:
        """Parse Claude's response into a dict with refined_prompt and annotations.

        Handles:
        - Raw JSON
        - JSON wrapped in ```json ... ``` fences
        - Fallback on parse failure
        """
        # Try direct parse first
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code fence
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding any JSON object in the text
        obj_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback — return the raw text as the refined prompt
        return {
            "refined_prompt": raw.strip() or "Claude returned an empty response.",
            "annotations": [
                {
                    "technique": "Parse error",
                    "reason": "Claude returned non-JSON. Showing raw output.",
                }
            ],
        }
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -v
```

Expected: all 6 tests PASS.

**Step 5: Commit**

```bash
git add engine.py tests/test_engine.py
git commit -m "feat: add RefinerEngine with prompt building and JSON parsing"
```

---

### Task 4: claude.py — Subprocess Wrapper

**Files:**
- Create: `claude.py`
- Create: `tests/test_claude.py`

**Step 1: Write failing tests**

```python
# tests/test_claude.py
import shutil
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
```

**Step 2: Run to verify they fail**

```bash
python -m pytest tests/test_claude.py -v
```

Expected: ImportError — claude module not found.

**Step 3: Implement claude.py**

```python
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
    """Run `claude -p <prompt> --model <model>` and return stdout.

    Raises:
        ClaudeNotFoundError: if claude binary is not in PATH.
        ClaudeError: if claude exits with non-zero return code.
    """
    if not check_claude_available():
        raise ClaudeNotFoundError(
            "claude CLI not found. Install Claude Code: "
            "https://claude.ai/code"
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
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_claude.py -v
```

Expected: all 5 tests PASS.

**Step 5: Commit**

```bash
git add claude.py tests/test_claude.py
git commit -m "feat: add claude subprocess wrapper with error handling"
```

---

### Task 5: app.py — Textual TUI Application

**Files:**
- Create: `app.py`

No unit tests for TUI (integration-tested manually in Task 7).

**Step 1: Implement app.py**

```python
# app.py
"""Textual TUI application for the Prompt Refiner."""

from __future__ import annotations

import pyperclip
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    Static,
    TextArea,
)

from claude import (
    MODELS,
    DEFAULT_MODEL,
    ClaudeError,
    ClaudeNotFoundError,
    next_model,
    run_claude,
)
from engine import RefinerEngine

# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
Screen {
    background: $surface;
}

#toolbar {
    height: 3;
    background: $primary;
    color: $text;
    align: left middle;
    padding: 0 1;
}

#toolbar Label {
    color: $text;
    text-style: bold;
    margin-right: 2;
}

#model-select {
    width: 28;
    margin-right: 2;
}

#panels {
    height: 1fr;
}

#input-panel {
    width: 1fr;
    border: solid $primary;
    padding: 0;
}

#input-label {
    background: $primary;
    color: $text;
    text-style: bold;
    padding: 0 1;
    height: 1;
}

#prompt-input {
    height: 1fr;
    border: none;
}

#output-panel {
    width: 1fr;
    border: solid $success;
    padding: 0;
}

#output-label {
    background: $success;
    color: $text;
    text-style: bold;
    padding: 0 1;
    height: 1;
}

#refined-output {
    height: 1fr;
    padding: 1;
}

#annotations-panel {
    height: 8;
    border: solid $warning;
    padding: 0;
}

#annotations-label {
    background: $warning;
    color: $text;
    text-style: bold;
    padding: 0 1;
    height: 1;
}

#annotations-log {
    height: 1fr;
    padding: 0 1;
}

#status-bar {
    height: 1;
    background: $panel;
    color: $text-muted;
    padding: 0 1;
}
"""

# ── App ───────────────────────────────────────────────────────────────────────


class PromptRefinerApp(App):
    """Interactive TUI for refining prompts using Claude."""

    CSS = CSS

    BINDINGS = [
        Binding("ctrl+enter", "refine", "Refine", show=True),
        Binding("y", "accept", "Accept", show=True),
        Binding("n", "reject", "Reject", show=True),
        Binding("e", "edit_refine", "Edit+Refine", show=True),
        Binding("tab", "cycle_model", "Cycle Model", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self._engine = RefinerEngine()
        self._current_model = DEFAULT_MODEL
        self._refined_text: str = ""
        self._is_refining = False

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        # Toolbar
        with Horizontal(id="toolbar"):
            yield Label("⚡ Prompt Refiner")
            yield Select(
                [(m, m) for m in MODELS],
                value=DEFAULT_MODEL,
                id="model-select",
            )

        # Main panels
        with Horizontal(id="panels"):
            with Vertical(id="input-panel"):
                yield Label("YOUR PROMPT", id="input-label")
                yield TextArea(id="prompt-input")

            with Vertical(id="output-panel"):
                yield Label("REFINED PROMPT", id="output-label")
                yield RichLog(id="refined-output", highlight=True, markup=True)

        # Annotations
        with Vertical(id="annotations-panel"):
            yield Label("ANNOTATIONS", id="annotations-label")
            yield RichLog(id="annotations-log", markup=True)

        # Status + Footer
        yield Static("", id="status-bar")
        yield Footer()

    # ── Event handlers ────────────────────────────────────────────────────────

    @on(Select.Changed, "#model-select")
    def on_model_changed(self, event: Select.Changed) -> None:
        self._current_model = str(event.value)
        self._set_status(f"Model: {self._current_model}")

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_cycle_model(self) -> None:
        """Cycle to the next model."""
        self._current_model = next_model(self._current_model)
        self.query_one("#model-select", Select).value = self._current_model
        self._set_status(f"Model switched to {self._current_model}")

    def action_refine(self) -> None:
        """Trigger prompt refinement."""
        if self._is_refining:
            return
        raw = self.query_one("#prompt-input", TextArea).text.strip()
        if not raw:
            self._set_status("⚠ Enter a prompt first.")
            return
        self._start_refine(raw, comment=None)

    def action_accept(self) -> None:
        """Copy refined prompt to clipboard."""
        if not self._refined_text:
            self._set_status("⚠ No refined prompt to accept.")
            return
        try:
            pyperclip.copy(self._refined_text)
            self._set_status("✓ Copied to clipboard!")
        except Exception:
            self._set_status("⚠ Clipboard unavailable. Showing in output panel.")

    def action_reject(self) -> None:
        """Clear the output panel and return focus to input."""
        self.query_one("#refined-output", RichLog).clear()
        self.query_one("#annotations-log", RichLog).clear()
        self._refined_text = ""
        self._set_status("Rejected. Enter a new prompt.")
        self.query_one("#prompt-input", TextArea).focus()

    def action_edit_refine(self) -> None:
        """Open comment dialog and refine with comment."""
        if not self._refined_text:
            self._set_status("⚠ Refine a prompt first, then use e to add comments.")
            return
        self.app.push_screen(CommentScreen(self._on_comment_submitted))

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _start_refine(self, raw: str, comment: str | None) -> None:
        """Clear output and start the background refinement worker."""
        self.query_one("#refined-output", RichLog).clear()
        self.query_one("#annotations-log", RichLog).clear()
        self._refined_text = ""
        self._is_refining = True
        self._set_status("⏳ Refining...")
        self._refine_worker(raw, comment)

    @work(thread=True)
    def _refine_worker(self, raw: str, comment: str | None) -> None:
        """Background thread: call claude and update UI."""
        try:
            full_prompt = self._engine.build_refiner_prompt(raw, comment)
            response = run_claude(full_prompt, self._current_model)
            parsed = self._engine.parse_response(response)
            self.call_from_thread(self._display_result, parsed)
        except ClaudeNotFoundError as exc:
            self.call_from_thread(self._set_status, f"✗ {exc}")
        except ClaudeError as exc:
            self.call_from_thread(self._set_status, f"✗ Claude error: {exc}")
        except Exception as exc:
            self.call_from_thread(self._set_status, f"✗ Unexpected error: {exc}")
        finally:
            self._is_refining = False

    def _display_result(self, parsed: dict) -> None:
        """Display the parsed refinement result in the TUI panels."""
        refined = parsed.get("refined_prompt", "")
        annotations = parsed.get("annotations", [])

        self._refined_text = refined

        output = self.query_one("#refined-output", RichLog)
        output.clear()
        output.write(refined)

        ann_log = self.query_one("#annotations-log", RichLog)
        ann_log.clear()
        for ann in annotations:
            technique = ann.get("technique", "")
            reason = ann.get("reason", "")
            ann_log.write(f"[bold yellow]►[/bold yellow] [bold]{technique}[/bold] — {reason}")

        self._set_status("Done! Press y=Accept  n=Reject  e=Edit+Refine")

    def _on_comment_submitted(self, comment: str) -> None:
        """Called when user submits a comment in the comment dialog."""
        raw = self.query_one("#prompt-input", TextArea).text.strip()
        if raw:
            self._start_refine(raw, comment=comment)

    def _set_status(self, message: str) -> None:
        self.query_one("#status-bar", Static).update(message)


# ── Comment Dialog Screen ─────────────────────────────────────────────────────

from textual.screen import Screen


class CommentScreen(Screen):
    """Modal screen for entering a refinement comment."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Cancel"),
    ]

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def compose(self) -> ComposeResult:
        yield Static(
            "\n[bold]Add a refinement comment[/bold]\n"
            "e.g. 'make it shorter', 'add more constraints', 'use XML tags'\n",
            markup=True,
        )
        yield Input(placeholder="Your comment...", id="comment-input")
        yield Static("\nEnter to submit  •  Esc to cancel\n")

    @on(Input.Submitted, "#comment-input")
    def on_submit(self, event: Input.Submitted) -> None:
        comment = event.value.strip()
        self.app.pop_screen()
        if comment:
            self._callback(comment)

    def action_dismiss_screen(self) -> None:
        self.app.pop_screen()
```

**Step 2: Commit**

```bash
git add app.py
git commit -m "feat: add Textual TUI with input/output/annotations panels"
```

---

### Task 6: main.py — Entry Point

**Files:**
- Create: `main.py`

**Step 1: Implement main.py**

```python
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
```

**Step 2: Run the app to verify it launches**

```bash
python main.py
```

Expected: TUI launches. Verify:
- Three panels visible (YOUR PROMPT / REFINED PROMPT / ANNOTATIONS)
- Model selector in toolbar shows `claude-sonnet-4-6`
- Footer shows keybindings

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add entry point with claude availability check"
```

---

### Task 7: End-to-End Manual Test

**Step 1: Launch the app**

```bash
python main.py
```

**Step 2: Test basic refinement**
1. Click in the left panel (YOUR PROMPT)
2. Type: `write a function to parse json`
3. Press `Ctrl+Enter`
4. Verify:
   - Status bar shows "⏳ Refining..."
   - After ~10-30s, right panel fills with refined prompt
   - Annotations panel shows techniques applied

**Step 3: Test Accept (y)**
1. After refinement, press `y`
2. Verify: status bar shows "✓ Copied to clipboard!"
3. Paste somewhere to verify clipboard content

**Step 4: Test Reject (n)**
1. Press `n`
2. Verify: right panel clears, cursor returns to input

**Step 5: Test Refine with comments (e)**
1. Refine a prompt first (Ctrl+Enter)
2. Press `e`
3. Type "make it more concise"
4. Press Enter
5. Verify: a new refinement runs with the comment

**Step 6: Test model cycling (Tab)**
1. Press `Tab`
2. Verify: model selector changes to next model in list

**Step 7: Final commit**

```bash
git add .
git commit -m "chore: complete prompt refiner v1.0"
```

---

## Run All Tests

```bash
python -m pytest tests/ -v
```

Expected: all tests pass (techniques + engine + claude modules).
