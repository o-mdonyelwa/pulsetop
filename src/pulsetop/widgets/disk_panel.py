from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..system import Snapshot, _human_bytes


class DiskPanel(Widget):
    """Per-mountpoint disk usage bars."""

    DEFAULT_CSS = """
    DiskPanel {
        height: 100%;
        border: round $primary;
        padding: 0 1;
    }
    DiskPanel > .title {
        text-style: bold;
        color: $accent;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("DISK", classes="title")
        yield Static(id="disk-body")

    def update_data(self, snap: Snapshot) -> None:
        bar_width = 20
        lines: list[str] = []
        for d in snap.disks:
            color = "green" if d.percent < 70 else "yellow" if d.percent < 90 else "red"
            filled = int(min(d.percent, 100) / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            mount = d.mountpoint if len(d.mountpoint) <= 16 else d.mountpoint[:15] + "…"
            lines.append(
                f"{mount:<16}[{color}]{bar}[/{color}] {d.percent:4.1f}%  "
                f"{_human_bytes(d.used)}/{_human_bytes(d.total)}"
            )
        self.query_one("#disk-body", Static).update("\n".join(lines) or "No mounted disks detected")
