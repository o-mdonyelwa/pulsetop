from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from .system import SystemMonitor
from .widgets.confirm_kill import ConfirmKillScreen
from .widgets.cpu_panel import CpuPanel
from .widgets.disk_panel import DiskPanel
from .widgets.info_bar import InfoBar
from .widgets.mem_panel import MemoryPanel
from .widgets.net_panel import NetworkPanel
from .widgets.proc_panel import ProcessPanel

DEFAULT_REFRESH_SECONDS = 1.5


class PulseTopApp(App):
    """A fast, good-looking terminal system monitor."""

    TITLE = "PULSETOP"
    SUB_TITLE = "real-time system pulse"

    CSS = """
    #dashboard {
        height: 1fr;
    }
    #row-top, #row-mid {
        height: 13;
    }
    CpuPanel, MemoryPanel, NetworkPanel, DiskPanel {
        width: 1fr;
        margin: 0 1 1 0;
    }
    ProcessPanel {
        height: 1fr;
        margin: 0 1 1 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "sort_cpu", "Sort: CPU"),
        ("m", "sort_mem", "Sort: MEM"),
        ("p", "sort_pid", "Sort: PID"),
        ("k", "terminate_selected", "Terminate"),
        ("K", "kill_selected", "Force-kill"),
    ]

    def __init__(self, refresh_seconds: float = DEFAULT_REFRESH_SECONDS) -> None:
        super().__init__()
        self.monitor = SystemMonitor()
        self.refresh_seconds = refresh_seconds

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self._tick()
        self.set_interval(self.refresh_seconds, self._tick)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield InfoBar()
        with Vertical(id="dashboard"):
            with Horizontal(id="row-top"):
                yield CpuPanel(id="cpu-panel")
                yield MemoryPanel(id="mem-panel")
            with Horizontal(id="row-mid"):
                yield NetworkPanel(id="net-panel")
                yield DiskPanel(id="disk-panel")
            yield ProcessPanel(id="proc-panel")
        yield Footer()

    def _tick(self) -> None:
        snap = self.monitor.snapshot()
        self.query_one(InfoBar).update_data(snap)
        self.query_one(CpuPanel).update_data(snap)
        self.query_one(MemoryPanel).update_data(snap)
        self.query_one(NetworkPanel).update_data(snap)
        self.query_one(DiskPanel).update_data(snap)
        self.query_one(ProcessPanel).update_data(snap)

    def action_sort_cpu(self) -> None:
        self.query_one(ProcessPanel).set_sort("cpu")

    def action_sort_mem(self) -> None:
        self.query_one(ProcessPanel).set_sort("mem")

    def action_sort_pid(self) -> None:
        self.query_one(ProcessPanel).set_sort("pid")

    def action_terminate_selected(self) -> None:
        self._confirm_kill(force=False)

    def action_kill_selected(self) -> None:
        self._confirm_kill(force=True)

    def _confirm_kill(self, force: bool) -> None:
        selection = self.query_one(ProcessPanel).selected
        if selection is None:
            self.notify("No process selected", severity="warning")
            return
        pid, name = selection

        def handle_result(confirmed: bool | None) -> None:
            if confirmed:
                ok, message = self.monitor.kill(pid, force=force)
                self.notify(message, severity="information" if ok else "error")

        self.push_screen(ConfirmKillScreen(pid, name, force), handle_result)


def main() -> None:
    PulseTopApp().run()


if __name__ == "__main__":
    main()
