"""K4NZA: the feeder never checks in with adsb.im (utils.agg_status.ImStatus)."""

from types import SimpleNamespace
from unittest.mock import patch

from utils import agg_status


def test_im_status_answers_locally_without_network():
    d = SimpleNamespace(previous_version="", adsbim_api_url="https://adsb.im/api")
    with patch.object(agg_status, "generic_get_json", side_effect=AssertionError("network call")):
        r = agg_status.ImStatus(d).check()
        assert r["latest_tag"] == "" and "advice" in r
        agg_status.ImStatus(d).check(True)


def test_im_status_still_clears_previous_version(tmp_path, monkeypatch):
    marker = tmp_path / "previous_version"
    marker.write_text("v1")
    monkeypatch.setattr(agg_status, "PREVIOUS_VERSION_FILE", marker)
    d = SimpleNamespace(previous_version="k4nza-v3.0.15-24")
    agg_status.ImStatus(d).check()
    assert d.previous_version == "" and not marker.exists()
