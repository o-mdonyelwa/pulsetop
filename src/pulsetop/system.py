"""System metrics collection.

Wraps `psutil` and produces immutable `Snapshot` objects on demand. Process
CPU% is only accurate across repeated calls on the *same* `psutil.Process`
object, so we keep a small cache keyed by PID instead of recreating Process
objects on every poll.
"""

from __future__ import annotations

import platform
import socket
import time
from dataclasses import dataclass

import psutil


@dataclass(frozen=True, slots=True)
class ProcInfo:
    pid: int
    name: str
    user: str
    cpu: float
    mem: float
    status: str


@dataclass(frozen=True, slots=True)
class DiskInfo:
    mountpoint: str
    percent: float
    used: int
    total: int


@dataclass(frozen=True, slots=True)
class Snapshot:
    cpu_total: float
    cpu_per_core: list[float]
    mem_percent: float
    mem_used: int
    mem_total: int
    swap_percent: float
    swap_used: int
    swap_total: int
    net_sent_rate: float
    net_recv_rate: float
    net_sent_total: int
    net_recv_total: int
    disks: list[DiskInfo]
    processes: list[ProcInfo]
    hostname: str
    os_name: str
    cpu_model: str
    core_count: int
    uptime_seconds: float


def _human_bytes(n: float) -> str:
    """Format a byte count as a short human-readable string."""
    n = float(n)
    for unit in ("B", "K", "M", "G", "T", "P"):
        if abs(n) < 1024.0:
            return f"{n:,.1f}{unit}" if unit != "B" else f"{n:,.0f}{unit}"
        n /= 1024.0
    return f"{n:,.1f}E"


def _human_duration(seconds: float) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


class SystemMonitor:
    """Polls live system metrics and tracks per-process CPU% over time."""

    def __init__(self, proc_cache_limit: int = 4000) -> None:
        self._proc_cache: dict[int, psutil.Process] = {}
        self._proc_cache_limit = proc_cache_limit
        self._last_net = psutil.net_io_counters()
        self._last_time = time.monotonic()
        self._boot_time = psutil.boot_time()

        self.hostname = socket.gethostname()
        self.os_name = f"{platform.system()} {platform.release()}".strip()
        self.cpu_model = self._detect_cpu_model()
        self.core_count = psutil.cpu_count(logical=True) or 1

        # Prime psutil's internal "since last call" state so the first real
        # reading isn't a meaningless 0.0 across the board.
        psutil.cpu_percent(percpu=True)
        for pid in psutil.pids():
            self._get_process(pid)

    @staticmethod
    def _detect_cpu_model() -> str:
        try:
            with open("/proc/cpuinfo", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
        return platform.processor() or platform.machine() or "Unknown CPU"

    def _get_process(self, pid: int) -> psutil.Process | None:
        proc = self._proc_cache.get(pid)
        if proc is not None:
            return proc
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(None)  # prime baseline for this process
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        self._proc_cache[pid] = proc
        return proc

    def kill(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """Terminate (or kill -9) a process by PID. Returns (ok, message)."""
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            if force:
                proc.kill()
            else:
                proc.terminate()
            return True, f"Sent {'SIGKILL' if force else 'SIGTERM'} to {name} ({pid})"
        except psutil.NoSuchProcess:
            return False, f"No such process: {pid}"
        except psutil.AccessDenied:
            return False, f"Permission denied for PID {pid}"
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"Failed to kill {pid}: {exc}"

    def snapshot(self) -> Snapshot:
        now = time.monotonic()
        elapsed = max(now - self._last_time, 1e-6)

        cpu_per_core = list(psutil.cpu_percent(percpu=True))
        cpu_total = sum(cpu_per_core) / len(cpu_per_core) if cpu_per_core else 0.0

        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()

        net = psutil.net_io_counters()
        sent_rate = (net.bytes_sent - self._last_net.bytes_sent) / elapsed
        recv_rate = (net.bytes_recv - self._last_net.bytes_recv) / elapsed
        self._last_net = net
        self._last_time = now

        disks: list[DiskInfo] = []
        seen_mounts: set[str] = set()
        noisy_fstypes = {"squashfs", "tmpfs", "devtmpfs", "overlay", "fuse.snapfuse"}
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint in seen_mounts:
                continue
            if part.fstype.lower() in noisy_fstypes:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            if usage.total < 1024**3:  # skip mounts under 1 GiB — usually noise
                continue
            seen_mounts.add(part.mountpoint)
            disks.append(DiskInfo(part.mountpoint, usage.percent, usage.used, usage.total))
        disks.sort(key=lambda d: -d.percent)

        processes: list[ProcInfo] = []
        current_pids: set[int] = set()
        for pid in psutil.pids():
            current_pids.add(pid)
            proc = self._get_process(pid)
            if proc is None:
                continue
            try:
                with proc.oneshot():
                    cpu = proc.cpu_percent(None)
                    name = proc.name() or "?"
                    try:
                        user = proc.username()
                    except (psutil.AccessDenied, KeyError):
                        user = "?"
                    mem = proc.memory_percent()
                    status = proc.status()
                processes.append(ProcInfo(pid, name, (user or "?")[:14], cpu, mem, status))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                self._proc_cache.pop(pid, None)
                continue

        # Prune cache entries for processes that have exited.
        if len(self._proc_cache) > self._proc_cache_limit or True:
            stale = [pid for pid in self._proc_cache if pid not in current_pids]
            for pid in stale:
                del self._proc_cache[pid]

        return Snapshot(
            cpu_total=cpu_total,
            cpu_per_core=cpu_per_core,
            mem_percent=vm.percent,
            mem_used=vm.used,
            mem_total=vm.total,
            swap_percent=sw.percent if sw.total else 0.0,
            swap_used=sw.used,
            swap_total=sw.total,
            net_sent_rate=sent_rate,
            net_recv_rate=recv_rate,
            net_sent_total=net.bytes_sent,
            net_recv_total=net.bytes_recv,
            disks=disks[:6],
            processes=processes,
            hostname=self.hostname,
            os_name=self.os_name,
            cpu_model=self.cpu_model,
            core_count=self.core_count,
            uptime_seconds=time.time() - self._boot_time,
        )


__all__ = [
    "SystemMonitor",
    "Snapshot",
    "ProcInfo",
    "DiskInfo",
    "_human_bytes",
    "_human_duration",
]
