from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Sparkline, Static

from ..system import Snapshot, _human_bytes


class NetworkPanel(Widget):
    """Upload/download throughput as twin sparklines."""

    DEFAULT_CSS = """
    NetworkPanel {
        height: 100%;
        border: round $primary;
        padding: 0 1;
    }
    NetworkPanel > .title {
        text-style: bold;
        color: $accent;
    }
    NetworkPanel Sparkline {
        height: 3;
    }
    NetworkPanel #net-down-label, NetworkPanel #net-up-label {
        color: $text-muted;
    }
    """

    def __init__(self, history: int = 80, **kwargs) -> None:
        super().__init__(**kwargs)
        self._down: deque[float] = deque([0.0] * history, maxlen=history)
        self._up: deque[float] = deque([0.0] * history, maxlen=history)

    def compose(self) -> ComposeResult:
        yield Static("NETWORK", classes="title")
        yield Static(id="net-down-label")
        yield Sparkline([0.0], id="net-down-spark")
        yield Static(id="net-up-label")
        yield Sparkline([0.0], id="net-up-spark")

    def update_data(self, snap: Snapshot) -> None:
        self._down.append(snap.net_recv_rate)
        self._up.append(snap.net_sent_rate)

        self.query_one("#net-down-spark", Sparkline).data = list(self._down)
        self.query_one("#net-up-spark", Sparkline).data = list(self._up)

        self.query_one("#net-down-label", Static).update(
            f"[cyan]↓ down[/cyan]  {_human_bytes(snap.net_recv_rate)}/s  "
            f"(total {_human_bytes(snap.net_recv_total)})"
        )
        self.query_one("#net-up-label", Static).update(
            f"[magenta]↑ up[/magenta]    {_human_bytes(snap.net_sent_rate)}/s  "
            f"(total {_human_bytes(snap.net_sent_total)})"
        )
