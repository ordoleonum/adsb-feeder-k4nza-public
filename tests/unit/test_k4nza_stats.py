"""Tests for the dashboard's live numbers just after the decoder restarts."""

import io
import json
from types import SimpleNamespace

import app as app_module

AdsbIm = app_module.AdsbIm


def _me(sample=None):
    me = SimpleNamespace(k4_round_rate=AdsbIm.k4_round_rate)
    if sample:
        me._k4_ac_sample = sample
    return me


def test_first_minute_counts_use_the_seconds_running():
    # readsb's "last minute" counters 52 s after a start: 5760 messages, 988 positions
    prom = io.StringIO("readsb_messages_valid 5760\nreadsb_position_count_total 988\nreadsb_uptime 52000\n")
    pps, mps = AdsbIm.k4_first_minute_rates(_me(), prom, 52)
    assert (pps, mps) == (19, 111)  # not 16 and 96 (divided by 60)
    # never divided by less than 10 s
    pps, mps = AdsbIm.k4_first_minute_rates(_me(), io.StringIO("readsb_messages_valid 50\nreadsb_position_count_total 9\n"), 2)
    assert (pps, mps) == (0.9, 5.0)


def test_rates_from_the_aircraft_list_before_stats_exist(tmp_path):
    path = tmp_path / "aircraft.json"
    path.write_text(
        json.dumps(
            {
                "now": 1000.0,
                "messages": 10300,
                "aircraft": [
                    {"hex": "a1", "lat": 1, "lon": 2, "seen_pos": 0.4},
                    {"hex": "a2", "lat": 1, "lon": 2, "seen_pos": 7},
                    {"hex": "a3", "lat": 1, "lon": 2, "seen_pos": 90},
                    {"hex": "a4"},
                ],
            }
        )
    )
    # an earlier reading 3 s before: 300 messages since then
    me = _me(sample=(997.0, 10000))
    got = AdsbIm.k4_rates_from_aircraft(me, "ultrafeeder", path=str(path))
    assert got == {"pps": 1, "mps": 100, "planes": 2}
    assert me._k4_ac_sample == (1000.0, 10300)


def test_rates_from_the_aircraft_list_need_the_file(tmp_path):
    assert AdsbIm.k4_rates_from_aircraft(_me(sample=(1.0, 1)), "ultrafeeder", path=str(tmp_path / "missing.json")) is None
