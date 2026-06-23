from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Sparkline, Static

from ..system import Snapshot

CORE_BARS = "▁▂▃▄▅▆▇█"


class CpuPanel(Widget):
    """Aggregate CPU history sparkline plus a live per-core bar grid."""

    DEFAULT_CSS = """
    CpuPanel {
        height: 100%;
        border: round $primary;
        padding: 0 1;
    }
    CpuPanel > .title {
        text-style: bold;
        color: $accent;
    }
    CpuPanel Sparkline {
        height: 3;
        margin-bottom: 1;
    }
    CpuPanel #cpu-cores {
        height: 1fr;
    }
    """

    def __init__(self, history: int = 80, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history: deque[float] = deque([0.0] * history, maxlen=history)

    def compose(self) -> ComposeResult:
        yield Static("CPU", classes="title")
        yield Sparkline([0.0], id="cpu-sparkline", summary_function=max)
        yield Static(id="cpu-summary")
        yield Static(id="cpu-cores")

    def update_data(self, snap: Snapshot) -> None:
        self._history.append(snap.cpu_total)
        self.query_one("#cpu-sparkline", Sparkline).data = list(self._history)

        self.query_one("#cpu-summary", Static).update(
            f"[b]{snap.cpu_total:5.1f}%[/b] avg across {snap.core_count} cores  ·  {snap.cpu_model}"
        )
        self.query_one("#cpu-cores", Static).update(self._render_cores(snap.cpu_per_core))

    @staticmethod
    def _render_cores(values: list[float]) -> str:
        per_row = 2 if len(values) > 8 else 1
        bar_width = 16
        lines: list[str] = []
        for i in range(0, len(values), per_row):
            cells = []
            for idx in range(i, min(i + per_row, len(values))):
                v = values[idx]
                color = "green" if v < 50 else "yellow" if v < 80 else "red"
                filled = int(min(v, 100) / 100 * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                cells.append(f"C{idx:<2} [{color}]{bar}[/{color}] {v:5.1f}%")
            lines.append("   ".join(cells))
        return "\n".join(lines)
