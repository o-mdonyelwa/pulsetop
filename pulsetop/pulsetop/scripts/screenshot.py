"""Regenerate the demo screenshots used in README.md.

Textual can export a pixel-perfect SVG of its own render output, so the
images in assets/ are real captures of the app running — not mockups.

Usage:
    python scripts/screenshot.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from pulsetop.app import PulseTopApp

ASSETS = Path(__file__).resolve().parent.parent / "assets"


async def capture(name: str, setup=None, size: tuple[int, int] = (140, 44)) -> None:
    ASSETS.mkdir(exist_ok=True)
    app = PulseTopApp(refresh_seconds=1.5)
    async with app.run_test(size=size) as pilot:
        await pilot.pause(2.0)
        if setup is not None:
            await setup(pilot)
        svg = app.export_screenshot(title="pulsetop")
        out = ASSETS / f"{name}.svg"
        out.write_text(svg)
        print(f"wrote {out}")


async def _open_kill_modal(pilot) -> None:
    await pilot.press("k")
    await pilot.pause(0.3)


async def main() -> None:
    await capture("dashboard")
    await capture("kill-confirm", setup=_open_kill_modal)


if __name__ == "__main__":
    asyncio.run(main())
