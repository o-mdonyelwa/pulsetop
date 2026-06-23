from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static

from ..system import Snapshot

_SORT_LABELS = {"cpu": "CPU%", "mem": "MEM%", "pid": "PID"}


class ProcessPanel(Widget):
    """Live process table — sortable, with terminate/kill actions."""

    DEFAULT_CSS = """
    ProcessPanel {
        border: round $primary;
        padding: 0 1;
    }
    ProcessPanel > .title {
        text-style: bold;
        color: $accent;
    }
    ProcessPanel DataTable {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sort_key: str = "cpu"

    def compose(self) -> ComposeResult:
        yield Static(id="proc-title", classes="title")
        table = DataTable(zebra_stripes=True, cursor_type="row", id="proc-table")
        table.add_columns("PID", "NAME", "USER", "CPU%", "MEM%", "STATUS")
        yield table

    def on_mount(self) -> None:
        self._refresh_title()

    def _refresh_title(self) -> None:
        self.query_one("#proc-title", Static).update(
            f"PROCESSES — sorted by {_SORT_LABELS[self.sort_key]}"
        )

    def set_sort(self, key: str) -> None:
        if key in _SORT_LABELS:
            self.sort_key = key
            self._refresh_title()

    def update_data(self, snap: Snapshot) -> None:
        table = self.query_one("#proc-table", DataTable)

        if self.sort_key == "pid":
            procs = sorted(snap.processes, key=lambda p: p.pid)
        elif self.sort_key == "mem":
            procs = sorted(snap.processes, key=lambda p: p.mem, reverse=True)
        else:
            procs = sorted(snap.processes, key=lambda p: p.cpu, reverse=True)
        procs = procs[:200]

        table.clear()
        for p in procs:
            table.add_row(
                str(p.pid),
                p.name[:28],
                p.user,
                f"{p.cpu:5.1f}",
                f"{p.mem:5.1f}",
                p.status,
                key=str(p.pid),
            )

    @property
    def selected(self) -> tuple[int, str] | None:
        """Return (pid, name) of the currently highlighted row, if any."""
        table = self.query_one("#proc-table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value is None:
                return None
            pid = int(row_key.value)
            row = table.get_row(row_key)
            name = str(row[1]) if row else str(pid)
            return pid, name
        except Exception:
            return None
