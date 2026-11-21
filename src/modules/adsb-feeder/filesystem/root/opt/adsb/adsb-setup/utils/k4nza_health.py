"""Pi health readings for the top bar: SD card space, SkyStats data size and
power supply. (The CPU temperature has its own, older endpoint.)

Everything here is cheap except the SkyStats size, which walks the database
folder; it is cached for 10 minutes. A small daily size history is kept so
the growth per month can be shown.
"""

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

SIZE_CACHE_SECONDS = 600
GROWTH_MIN_DAYS = 7  # don't guess a monthly growth from less than a week
HISTORY_DAYS = 60

# vcgencmd get_throttled bits
UNDER_VOLTAGE_NOW = 1 << 0
THROTTLED_NOW = 1 << 2
UNDER_VOLTAGE_SINCE_BOOT = 1 << 16
THROTTLED_SINCE_BOOT = 1 << 18

_size_lock = threading.Lock()
_size_cache: dict = {"t": 0.0, "bytes": None}


def sd_usage(path: str = "/") -> dict:
    try:
        u = shutil.disk_usage(path)
    except OSError:
        return {"free_bytes": None, "total_bytes": None, "state": "unknown"}
    return {"free_bytes": u.free, "total_bytes": u.total, "state": sd_state(u.free, u.total)}


def sd_state(free: int, total: int) -> str:
    gb = 1024**3
    if total <= 0:
        return "unknown"
    pct = free * 100 / total
    if free < 1 * gb or pct < 5:
        return "bad"
    if free < 2 * gb or pct < 10:
        return "warn"
    return "ok"


def folder_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda e: None):
        for name in files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                pass
    return total


def _load_history(history_file: Path) -> dict:
    try:
        data = json.loads(history_file.read_text())
        return {k: int(v) for k, v in data.items()}
    except (OSError, ValueError, AttributeError):
        return {}


def record_size(history_file: Path, size: int, today: str) -> dict:
    """Remember one size per day (the newest), keeping about two months."""
    history = _load_history(history_file)
    history[today] = size
    for day in sorted(history)[:-HISTORY_DAYS]:
        del history[day]
    try:
        tmp = history_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(history))
        os.replace(tmp, history_file)
    except OSError:
        pass
    return history


def growth_per_month(history: dict, today: str):
    """Bytes per 30 days from the oldest sample in the last two months, or None."""
    if not history:
        return None
    days = sorted(history)
    oldest = days[0]
    try:
        span = (time.mktime(time.strptime(today, "%Y-%m-%d")) - time.mktime(time.strptime(oldest, "%Y-%m-%d"))) / 86400
    except ValueError:
        return None
    if span < GROWTH_MIN_DAYS or today not in history:
        return None
    return int((history[today] - history[oldest]) * 30 / span)


def skystats_size(data_path: str, history_file: Path, now: Optional[float] = None) -> dict:
    now = time.time() if now is None else now
    with _size_lock:
        if _size_cache["bytes"] is None or now - _size_cache["t"] > SIZE_CACHE_SECONDS:
            p = Path(data_path) if data_path else None
            size = folder_size(p) if p and p.is_dir() else None
            _size_cache.update(t=now, bytes=size)
            if size is not None:
                _size_cache["history"] = record_size(history_file, size, time.strftime("%Y-%m-%d", time.localtime(now)))
        size = _size_cache["bytes"]
        history = _size_cache.get("history", {})
    if size is None:
        return {"bytes": None, "growth_per_month_bytes": None}
    return {
        "bytes": size,
        "growth_per_month_bytes": growth_per_month(history, time.strftime("%Y-%m-%d", time.localtime(now))),
    }


def parse_throttled(text: str):
    """'throttled=0x50005' -> 0x50005, or None."""
    try:
        return int(text.strip().split("=", 1)[1], 16)
    except (IndexError, ValueError):
        return None


def read_throttled():
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return parse_throttled(out.stdout)


POWER_WARN_SECONDS = 24 * 3600


def power_status(throttled, undervoltage_seen: bool, undervoltage_epoch: float, now_ts: Optional[float] = None) -> dict:
    """bad: low voltage right now; warn: low voltage in the last day (or at an
    unknown time since boot); ok; unknown: not a Raspberry Pi (nothing to read)."""
    now_ts = time.time() if now_ts is None else now_ts
    last = undervoltage_epoch if undervoltage_epoch and undervoltage_epoch > 0 else None
    if throttled is None:
        if undervoltage_seen:
            return {"state": "warn", "now": False, "since_boot": True, "last_epoch": last, "throttled": False}
        return {"state": "unknown", "now": False, "since_boot": False, "last_epoch": last, "throttled": False}
    now = bool(throttled & UNDER_VOLTAGE_NOW)
    since_boot = bool(throttled & UNDER_VOLTAGE_SINCE_BOOT) or undervoltage_seen
    # the "since boot" flag never clears until a restart; after a quiet day
    # the reading goes back to OK (the tooltip still mentions it)
    recent = since_boot and (last is None or now_ts - last < POWER_WARN_SECONDS)
    state = "bad" if now else ("warn" if recent else "ok")
    return {
        "state": state,
        "now": now,
        "since_boot": since_boot,
        "last_epoch": last,
        "throttled": bool(throttled & (THROTTLED_NOW | THROTTLED_SINCE_BOOT)),
    }
