from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..system import Snapshot, _human_duration


class InfoBar(Widget):
    """Slim status strip: hostname, OS, uptime."""

    DEFAULT_CSS = """
    InfoBar {
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="info-text")

    def update_data(self, snap: Snapshot) -> None:
        self.query_one("#info-text", Static).update(
            f"[b]{snap.hostname}[/b]  ·  {snap.os_name}  ·  "
            f"up {_human_duration(snap.uptime_seconds)}  ·  "
            f"{len(snap.processes)} processes"
        )
