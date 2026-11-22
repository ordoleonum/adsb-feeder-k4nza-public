"""Tests for the route that serves the K4NZA live-map styling to tar1090."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import app as app_module
from flask import Flask


def _call(tmp_path, name):
    (tmp_path / "k4nza" / "map").mkdir(parents=True, exist_ok=True)
    (tmp_path / "k4nza" / "map" / "map.css").write_text("html.k4m{}")
    (tmp_path / "k4nza" / "map" / "map.js").write_text("console.log(1)")
    flask_app = Flask(__name__)
    with flask_app.test_request_context(), patch.object(app_module, "get_adsb_base_dir", return_value=str(tmp_path)):
        resp = app_module.AdsbIm.k4nza_map_file(None, name)
        resp.direct_passthrough = False
        return resp.status_code, resp.mimetype, resp.headers.get("Access-Control-Allow-Origin"), resp.get_data(as_text=True)


def test_serves_css_and_js(tmp_path):
    assert _call(tmp_path, "map.css") == (200, "text/css", "*", "html.k4m{}")
    code, mimetype, _, body = _call(tmp_path, "map.js")
    assert (code, mimetype, body) == (200, "application/javascript", "console.log(1)")


def test_only_known_files(tmp_path):
    assert _call(tmp_path, "secret.txt")[0] == 404
    assert _call(tmp_path, "..")[0] == 404


class _D:
    def __init__(self, skystats=True):
        self.skystats = skystats

    def is_enabled(self, name):
        return self.skystats if name == "skystats" else False

    def env_by_tags(self, tag):
        class _E:
            value = 5173

        return _E()


class _Resp:
    def __init__(self, code, data):
        self.status_code = code
        self._data = data

    def json(self):
        return self._data


def _route(callsign, skystats=True, get=None):
    from types import SimpleNamespace

    me = SimpleNamespace(_d=_D(skystats))
    flask_app = Flask(__name__)
    with flask_app.test_request_context(), patch.object(app_module.requests, "get", get or (lambda *a, **k: _Resp(404, {}))):
        resp = app_module.AdsbIm.k4nza_route(me, callsign)
        return resp.status_code, resp.headers.get("Access-Control-Allow-Origin"), resp.get_json()


def test_route_comes_from_skystats():
    seen = {}

    def get(url, timeout):
        seen["url"] = url
        return _Resp(200, {"callsign": "SWA2039", "origin": {"iata": "MCI"}, "destination": {"iata": "DAL"}})

    code, cors, body = _route("swa2039", get=get)
    assert (code, cors) == (200, "*")
    assert body["destination"]["iata"] == "DAL"
    assert seen["url"] == "http://127.0.0.1:5173/api/route/SWA2039"


def test_route_without_skystats_or_bad_callsign():
    assert _route("SWA2039", skystats=False)[0] == 404
    assert _route("bad!")[0] == 400
    assert _route("AAL1")[0] == 404


def test_serves_the_bundled_fonts_with_cors(tmp_path):
    fonts = tmp_path / "adsb-setup" / "static" / "fonts"
    fonts.mkdir(parents=True)
    (fonts / "plus-jakarta-sans-latin-wght.woff2").write_bytes(b"wOF2")
    code, mimetype, cors, _ = _call(tmp_path, "plus-jakarta-sans-latin-wght.woff2")
    assert (code, mimetype, cors) == (200, "font/woff2", "*")
    # only the listed fonts, nothing else from static/
    (fonts / "LICENSE.txt").write_text("x")
    assert _call(tmp_path, "LICENSE.txt")[0] == 404


def _home(skystats=True, get=None, query=""):
    from types import SimpleNamespace

    me = SimpleNamespace(_d=_D(skystats), k4_feeder_tz=lambda: ZoneInfo("America/Chicago"))
    flask_app = Flask(__name__)
    with flask_app.test_request_context("/api/k4nza/home" + query), patch.object(app_module.requests, "get", get or (lambda *a, **k: _Resp(500, {}))):
        resp = app_module.AdsbIm.k4nza_home(me)
        return resp.status_code, resp.get_json()


def test_home_summary_comes_from_skystats_in_the_feeder_timezone():
    seen = {}

    def get(url, params, timeout):
        seen["url"], seen["params"] = url, params
        return _Resp(200, {"aircraft_today": 3, "new_today": 2})

    code, body = _home(get=get)
    assert code == 200 and body["new_today"] == 2
    assert seen["url"] == "http://127.0.0.1:5173/api/k4nza/home"
    assert seen["params"] == {"tz": "America/Chicago"}
    # the hour bars follow the station's clock, not the viewing device's
    assert body["now_hour"] == datetime.now(ZoneInfo("America/Chicago")).hour


def test_home_week_and_month_pass_the_days_through():
    seen = {}

    def get(url, params, timeout):
        seen["params"] = params
        return _Resp(200, {"daily": []})

    assert _home(get=get, query="?days=30")[0] == 200
    assert seen["params"] == {"tz": "America/Chicago", "days": "30"}
    # anything else is the normal "today" summary
    _home(get=get, query="?days=9999")
    assert seen["params"] == {"tz": "America/Chicago"}


def test_home_summary_without_skystats():
    assert _home(skystats=False)[0] == 404
    assert _home()[0] == 502


def test_closest_aircraft_for_the_home_page():
    aircraft = [
        {"hex": "a1", "r_dst": 40.0, "seen_pos": 2, "alt_baro": 30000, "flight": "SWA1  ", "extra": 1},
        {"hex": "a2", "r_dst": 5.0, "seen_pos": 1, "alt_baro": "ground"},
        {"hex": "a3", "r_dst": 1.0, "seen_pos": 120},   # position too old
        {"hex": "a4", "seen_pos": 1},                    # no distance
        {"hex": "a5", "r_dst": 12.0, "seen_pos": 5},
    ]
    got = app_module.AdsbIm.k4nza_pick_closest(aircraft)
    assert [a["hex"] for a in got] == ["a2", "a5", "a1"]
    assert "extra" not in got[2] and got[2]["flight"] == "SWA1  "
