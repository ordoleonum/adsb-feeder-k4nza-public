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
