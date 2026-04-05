# app.py
"""Textual TUI application for the Prompt Refiner."""

from __future__ import annotations

import pyperclip
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Footer,
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


class CommentScreen(Screen):
    """Modal screen for entering a refinement comment."""

    BINDINGS = [Binding("escape", "dismiss_screen", "Cancel")]

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

    def compose(self) -> ComposeResult:
        with Horizontal(id="toolbar"):
            yield Label("⚡ Prompt Refiner")
            yield Select(
                [(m, m) for m in MODELS],
                value=DEFAULT_MODEL,
                id="model-select",
            )
        with Horizontal(id="panels"):
            with Vertical(id="input-panel"):
                yield Label("YOUR PROMPT", id="input-label")
                yield TextArea(id="prompt-input")
            with Vertical(id="output-panel"):
                yield Label("REFINED PROMPT", id="output-label")
                yield RichLog(id="refined-output", highlight=True, markup=True)
        with Vertical(id="annotations-panel"):
            yield Label("ANNOTATIONS", id="annotations-label")
            yield RichLog(id="annotations-log", markup=True)
        yield Static("", id="status-bar")
        yield Footer()

    @on(Select.Changed, "#model-select")
    def on_model_changed(self, event: Select.Changed) -> None:
        self._current_model = str(event.value)
        self._set_status(f"Model: {self._current_model}")

    def action_cycle_model(self) -> None:
        self._current_model = next_model(self._current_model)
        self.query_one("#model-select", Select).value = self._current_model
        self._set_status(f"Model switched to {self._current_model}")

    def action_refine(self) -> None:
        if self._is_refining:
            return
        raw = self.query_one("#prompt-input", TextArea).text.strip()
        if not raw:
            self._set_status("⚠ Enter a prompt first.")
            return
        self._start_refine(raw, comment=None)

    def action_accept(self) -> None:
        if not self._refined_text:
            self._set_status("⚠ No refined prompt to accept.")
            return
        try:
            pyperclip.copy(self._refined_text)
            self._set_status("✓ Copied to clipboard!")
        except Exception:
            self._set_status("⚠ Clipboard unavailable. Showing in output panel.")

    def action_reject(self) -> None:
        self.query_one("#refined-output", RichLog).clear()
        self.query_one("#annotations-log", RichLog).clear()
        self._refined_text = ""
        self._set_status("Rejected. Enter a new prompt.")
        self.query_one("#prompt-input", TextArea).focus()

    def action_edit_refine(self) -> None:
        if not self._refined_text:
            self._set_status("⚠ Refine a prompt first, then use e to add comments.")
            return
        self.app.push_screen(CommentScreen(self._on_comment_submitted))

    def _start_refine(self, raw: str, comment: str | None) -> None:
        self.query_one("#refined-output", RichLog).clear()
        self.query_one("#annotations-log", RichLog).clear()
        self._refined_text = ""
        self._is_refining = True
        self._set_status("⏳ Refining...")
        self._refine_worker(raw, comment)

    @work(thread=True)
    def _refine_worker(self, raw: str, comment: str | None) -> None:
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
        raw = self.query_one("#prompt-input", TextArea).text.strip()
        if raw:
            self._start_refine(raw, comment=comment)

    def _set_status(self, message: str) -> None:
        self.query_one("#status-bar", Static).update(message)
