"""Tests for the route that serves the K4NZA live-map styling to tar1090."""

from unittest.mock import patch

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
