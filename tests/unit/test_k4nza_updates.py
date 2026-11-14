"""Tests for the K4NZA Raspberry Pi OS update check."""

import subprocess
from unittest.mock import patch

from utils import k4nza_updates


def _done(stdout="", rc=0):
    return subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr="")


SIMULATION = """Reading package lists...
Inst libc6 [2.41-11] (2.41-12 Debian:13.2/stable [arm64])
Inst raspi-firmware [1:1.20250430] (1:1.20251001 Raspberry Pi Foundation:stable [arm64])
Conf libc6 (2.41-12 Debian:13.2/stable [arm64])
"""


def test_os_check_counts_waiting_packages():
    k4nza_updates.os_forget()
    with patch.object(k4nza_updates.subprocess, "run", side_effect=[_done(), _done(SIMULATION)]):
        k4nza_updates._run_os_check()
    s = k4nza_updates.os_status(start_check=False)
    assert s["count"] == 2
    assert s["packages"] == ["libc6", "raspi-firmware"]
    assert s["error"] == ""
    assert s["checking"] is False
    assert s["checked_ago"] == "just now"


def test_os_check_reports_offline():
    k4nza_updates.os_forget()
    with patch.object(k4nza_updates.subprocess, "run", side_effect=[_done(rc=100), _done("")]):
        k4nza_updates._run_os_check()
    s = k4nza_updates.os_status(start_check=False)
    assert s["count"] == 0
    assert "online" in s["error"]


def test_os_check_survives_missing_apt():
    k4nza_updates.os_forget()
    with patch.object(k4nza_updates.subprocess, "run", side_effect=FileNotFoundError("apt-get")):
        k4nza_updates._run_os_check()
    s = k4nza_updates.os_status(start_check=False)
    assert s["count"] is None
    assert "FileNotFoundError" in s["error"]


def test_os_check_not_repeated_while_fresh():
    k4nza_updates.os_forget()
    with patch.object(k4nza_updates.subprocess, "run", side_effect=[_done(), _done("")]):
        k4nza_updates._run_os_check()
    with patch.object(k4nza_updates.threading, "Thread") as thread:
        k4nza_updates.os_check()
        thread.assert_not_called()
        k4nza_updates.os_check(force=True)
        thread.assert_called_once()
    k4nza_updates._os["running"] = False


class _Resp:
    def __init__(self, code, data=None):
        self.status_code = code
        self._data = data or {}

    def json(self):
        return self._data


def test_feeder_update_available_without_key(tmp_path):
    (tmp_path / "k4nza.version").write_text("k4nza-v3.0.15-7\n")
    k4nza_updates.clear_cache()
    release = _Resp(200, {"tag_name": "k4nza-v3.0.15-8"})
    with patch.object(k4nza_updates, "get_adsb_base_dir", return_value=str(tmp_path)):
        with patch.object(k4nza_updates.requests, "get", return_value=release) as get:
            s = k4nza_updates.status(refresh=True)
    assert s == {
        "installed": "k4nza-v3.0.15-7",
        "latest": "k4nza-v3.0.15-8",
        "published": "",
        "error": "",
        "update_available": True,
        "notes_html": "",
        "previous": "",
    }
    url = get.call_args[0][0]
    assert url.endswith("/repos/ordoleonum/adsb-feeder-k4nza-public/releases/latest")
    assert "Authorization" not in get.call_args[1]["headers"]


def test_feeder_no_release_yet(tmp_path):
    k4nza_updates.clear_cache()
    with patch.object(k4nza_updates, "get_adsb_base_dir", return_value=str(tmp_path)):
        with patch.object(k4nza_updates.requests, "get", return_value=_Resp(404)):
            s = k4nza_updates.status(refresh=True)
    assert s["installed"] == "unknown"
    assert s["update_available"] is False
    assert "No K4NZA release" in s["error"]


def test_restart_blocked_while_os_update_runs():
    with patch.object(k4nza_updates.subprocess, "run", return_value=_done("active")):
        assert k4nza_updates.os_update_running() is True
    with patch.object(k4nza_updates.subprocess, "run", return_value=_done("inactive", rc=3)):
        assert k4nza_updates.os_update_running() is False
    with patch.object(k4nza_updates.subprocess, "run", side_effect=FileNotFoundError("systemctl")):
        assert k4nza_updates.os_update_running() is False


def test_os_check_uses_plain_upgrade():
    k4nza_updates.os_forget()
    with patch.object(k4nza_updates.subprocess, "run", side_effect=[_done(), _done("")]) as run:
        k4nza_updates._run_os_check()
    sim = run.call_args_list[1][0][0]
    assert sim[-1] == "upgrade" and "--with-new-pkgs" not in sim


# ---------------------------------------------------------------------------
# rollback ("Go back to ...") and release notes


def test_previous_version_offered_only_for_kept_releases(tmp_path, monkeypatch):
    monkeypatch.setattr(k4nza_updates, "_base", lambda: tmp_path)
    (tmp_path / "k4nza.version").write_text("k4nza-v3.0.15-21\n")
    assert k4nza_updates.previous_version() == ""  # nothing recorded yet

    (tmp_path / "k4nza.version.prev").write_text("k4nza-v3.0.15-20\n")
    assert k4nza_updates.previous_version() == "k4nza-v3.0.15-20"

    # releases before -20 didn't keep their tags, so they can't be reinstalled
    (tmp_path / "k4nza.version.prev").write_text("k4nza-v3.0.15-14\n")
    assert k4nza_updates.previous_version() == ""

    # never offer the version that is already installed, or junk
    (tmp_path / "k4nza.version.prev").write_text("k4nza-v3.0.15-21\n")
    assert k4nza_updates.previous_version() == ""
    (tmp_path / "k4nza.version.prev").write_text("k4nza-v3.0.15-20; reboot\n")
    assert k4nza_updates.previous_version() == ""


def test_request_version_writes_target_for_feeder_update(tmp_path, monkeypatch):
    monkeypatch.setattr(k4nza_updates, "_base", lambda: tmp_path)
    assert k4nza_updates.request_version("k4nza-v3.0.15-20") is True
    assert (tmp_path / "k4nza-update-target").read_text() == "k4nza-v3.0.15-20\n"
    assert k4nza_updates.request_version("../../etc/passwd") is False


def test_render_notes_is_safe_and_stops_at_install_note():
    html = k4nza_updates.render_notes(
        "**New**\n"
        "- **Search** for `N812DN` ([details](https://example.com/a?b=1&c=2))\n"
        "  more text\n"
        "- <script>alert(1)</script> [x](javascript:alert(1))\n"
        "\n---\n\n**Install:** download the image\n"
    )
    assert "<p><strong>New</strong></p>" in html
    assert "<li><strong>Search</strong> for <code>N812DN</code>" in html
    assert 'href="https://example.com/a?b=1&amp;c=2"' in html
    assert "more text</li>" in html
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert 'href="javascript' not in html
    assert "Install" not in html
    assert html.count("<ul>") == html.count("</ul>") == 1


def test_render_notes_joins_wrapped_paragraph_lines():
    html = k4nza_updates.render_notes("First line of a paragraph\ncontinues here.\n\nSecond paragraph.\n")
    assert html == "<p>First line of a paragraph continues here.</p>\n<p>Second paragraph.</p>"
