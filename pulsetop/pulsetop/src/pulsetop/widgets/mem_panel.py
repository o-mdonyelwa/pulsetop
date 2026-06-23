from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import ProgressBar, Static

from ..system import Snapshot, _human_bytes


class MemoryPanel(Widget):
    """RAM and swap usage as labelled progress bars."""

    DEFAULT_CSS = """
    MemoryPanel {
        height: 100%;
        border: round $primary;
        padding: 0 1;
    }
    MemoryPanel > .title {
        text-style: bold;
        color: $accent;
    }
    MemoryPanel ProgressBar {
        width: 1fr;
        margin-bottom: 1;
    }
    MemoryPanel Static.label {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("MEMORY", classes="title")
        yield Static(id="mem-label", classes="label")
        yield ProgressBar(total=100, id="mem-bar", show_eta=False)
        yield Static(id="swap-label", classes="label")
        yield ProgressBar(total=100, id="swap-bar", show_eta=False)

    def update_data(self, snap: Snapshot) -> None:
        self.query_one("#mem-bar", ProgressBar).update(progress=snap.mem_percent)
        self.query_one("#mem-label", Static).update(
            f"RAM   {_human_bytes(snap.mem_used)} / {_human_bytes(snap.mem_total)}"
        )

        self.query_one("#swap-bar", ProgressBar).update(progress=snap.swap_percent)
        swap_text = (
            f"SWAP  {_human_bytes(snap.swap_used)} / {_human_bytes(snap.swap_total)}"
            if snap.swap_total
            else "SWAP  none configured"
        )
        self.query_one("#swap-label", Static).update(swap_text)
