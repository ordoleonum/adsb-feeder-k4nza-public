"""Tests for the top-bar Pi health readings."""

import time

from utils import k4nza_health

GB = 1024**3


def test_sd_state_thresholds():
    assert k4nza_health.sd_state(20 * GB, 29 * GB) == "ok"
    assert k4nza_health.sd_state(int(1.5 * GB), 29 * GB) == "warn"  # under 2 GB
    assert k4nza_health.sd_state(int(0.8 * GB), 29 * GB) == "bad"  # under 1 GB
    assert k4nza_health.sd_state(int(2.5 * GB), 64 * GB) == "bad"  # under 5 %
    assert k4nza_health.sd_state(1, 0) == "unknown"


def test_parse_throttled():
    assert k4nza_health.parse_throttled("throttled=0x50005\n") == 0x50005
    assert k4nza_health.parse_throttled("throttled=0x0") == 0
    assert k4nza_health.parse_throttled("garbage") is None


def test_power_status():
    now = 1_800_000_000.0
    # not a Pi (no vcgencmd) and nothing seen: hide the reading
    assert k4nza_health.power_status(None, False, 0, now)["state"] == "unknown"
    assert k4nza_health.power_status(0, False, 0, now)["state"] == "ok"
    # low voltage right now
    p = k4nza_health.power_status(0x50005, False, 0, now)
    assert p["state"] == "bad" and p["now"] and p["throttled"]
    # earlier since boot, time unknown -> warn
    assert k4nza_health.power_status(0x50000, False, 0, now)["state"] == "warn"
    # seen an hour ago -> warn, with the time
    p = k4nza_health.power_status(0x50000, True, now - 3600, now)
    assert p["state"] == "warn" and p["last_epoch"] == now - 3600
    # quiet for more than a day -> back to OK, but still remembered
    p = k4nza_health.power_status(0x50000, True, now - 2 * 86400, now)
    assert p["state"] == "ok" and p["since_boot"]


def test_growth_per_month(tmp_path):
    f = tmp_path / "sizes.json"
    k4nza_health.record_size(f, 1000 * 1024**2, "2026-10-01")
    h = k4nza_health.record_size(f, 1060 * 1024**2, "2026-10-04")
    assert k4nza_health.growth_per_month(h, "2026-10-04") is None  # less than a week
    h = k4nza_health.record_size(f, 1300 * 1024**2, "2026-10-31")
    assert k4nza_health.growth_per_month(h, "2026-10-31") == 300 * 1024**2
    # the history is trimmed to about two months
    for d in range(70):
        h = k4nza_health.record_size(f, d, time.strftime("%Y-%m-%d", time.gmtime(1_800_000_000 + d * 86400)))
    assert len(h) == k4nza_health.HISTORY_DAYS


def test_skystats_size_missing_folder(tmp_path):
    k4nza_health._size_cache.update(t=0.0, bytes=None)
    r = k4nza_health.skystats_size(str(tmp_path / "nope"), tmp_path / "h.json")
    assert r == {"bytes": None, "growth_per_month_bytes": None}
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "a").write_bytes(b"x" * 1000)
    k4nza_health._size_cache.update(t=0.0, bytes=None)
    r = k4nza_health.skystats_size(str(tmp_path / "db"), tmp_path / "h.json")
    assert r["bytes"] == 1000
