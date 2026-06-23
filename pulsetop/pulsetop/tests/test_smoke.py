"""Smoke and unit tests for pulsetop.

Run with: pytest
"""

from __future__ import annotations

import asyncio

from pulsetop.app import PulseTopApp
from pulsetop.system import SystemMonitor, _human_bytes, _human_duration


def test_app_boots_and_renders_without_exceptions() -> None:
    async def run() -> None:
        app = PulseTopApp(refresh_seconds=5)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            assert app.is_running

    asyncio.run(run())


def test_sort_keybindings_change_process_sort() -> None:
    async def run() -> None:
        from pulsetop.widgets.proc_panel import ProcessPanel

        app = PulseTopApp(refresh_seconds=5)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            panel = app.query_one(ProcessPanel)
            assert panel.sort_key == "cpu"
            await pilot.press("m")
            assert panel.sort_key == "mem"
            await pilot.press("p")
            assert panel.sort_key == "pid"

    asyncio.run(run())


def test_kill_confirmation_modal_opens_and_cancels() -> None:
    async def run() -> None:
        app = PulseTopApp(refresh_seconds=5)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("k")
            await pilot.pause(0.2)
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause(0.2)
            assert len(app.screen_stack) == 1

    asyncio.run(run())


def test_system_monitor_snapshot_has_sane_values() -> None:
    monitor = SystemMonitor()
    snap = monitor.snapshot()

    assert snap.mem_total > 0
    assert 0.0 <= snap.mem_percent <= 100.0
    assert snap.core_count >= 1
    assert isinstance(snap.processes, list)
    assert len(snap.processes) > 0
    assert snap.hostname


def test_human_formatters() -> None:
    assert _human_bytes(0) == "0B"
    assert _human_bytes(1536).startswith("1.5K")
    assert _human_duration(59) == "0m"
    assert _human_duration(3700) == "1h 1m"
