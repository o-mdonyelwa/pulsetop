from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmKillScreen(ModalScreen[bool]):
    """Yes/No confirmation before sending a signal to a process."""

    DEFAULT_CSS = """
    ConfirmKillScreen {
        align: center middle;
    }
    ConfirmKillScreen > Vertical {
        width: 56;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    ConfirmKillScreen Static {
        margin-bottom: 1;
        text-align: center;
    }
    ConfirmKillScreen Horizontal {
        align: center middle;
        height: auto;
    }
    ConfirmKillScreen Button {
        margin: 0 1;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, pid: int, name: str, force: bool) -> None:
        super().__init__()
        self.pid = pid
        self.proc_name = name
        self.force = force

    def compose(self) -> ComposeResult:
        verb = "send SIGKILL to" if self.force else "terminate"
        with Vertical():
            yield Static(f"Really {verb}\n[b]{self.proc_name}[/b] (PID {self.pid})?")
            with Horizontal():
                yield Button("Cancel", id="cancel")
                yield Button("Confirm", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_cancel(self) -> None:
        self.dismiss(False)
