"""Tests for the nightly NAS backup (scheduling, settings, pruning, the backup run itself)."""

import os
import stat
from datetime import datetime
from unittest.mock import patch

import pytest
from utils import k4nza_nas_backup as nas

GOOD = {
    "enabled": True,
    "host": "192.168.1.50",
    "share": "k4nza-backup",
    "folder": "",
    "user": "k4nza",
    "password": "p@ss, word=1",
    "time": "03:00",
    "keep": 3,
}


def test_validate_accepts_good_settings():
    assert nas.validate(GOOD) == []
    assert nas.validate(dict(GOOD, host="DS1522.local", folder="Pi 5 feeder")) == []


@pytest.mark.parametrize(
    "change",
    [
        {"host": ""},
        {"host": "nas;rm -rf /"},
        {"share": "a/b"},
        {"share": "a,b"},
        {"folder": ".."},
        {"folder": "a/b"},
        {"user": ""},
        {"user": "a,uid=0"},
        {"password": ""},
        {"password": "a\nusername=x"},
        {"time": "3am"},
        {"time": "24:00"},
        {"keep": 0},
        {"keep": "x"},
    ],
)
def test_validate_rejects_bad_settings(change):
    assert nas.validate(dict(GOOD, **change))


def test_settings_round_trip_and_password_file_is_private(tmp_path):
    nas.save_settings(tmp_path, GOOD)
    assert nas.load_settings(tmp_path) == GOOD
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(tmp_path / nas.SETTINGS_NAME).st_mode) == 0o600
    shown = nas.public_settings(GOOD)
    assert "password" not in shown and shown["has_password"] is True


def test_load_settings_defaults_when_missing_or_broken(tmp_path):
    assert nas.load_settings(tmp_path) == nas.DEFAULTS
    (tmp_path / nas.SETTINGS_NAME).write_text("not json")
    assert nas.load_settings(tmp_path) == nas.DEFAULTS


def test_due_only_inside_the_window_and_once_per_night():
    at = datetime(2026, 11, 14, 3, 0, 30)
    assert nas.due(GOOD, {}, datetime(2026, 11, 14, 2, 59)) is None
    slot = nas.due(GOOD, {}, at)
    assert slot == "2026-11-14 03:00"
    assert nas.due(GOOD, {"done_slot": slot}, at) is None
    # Pi was off at 3 am: still runs later that morning, but not 13 hours later
    assert nas.due(GOOD, {}, datetime(2026, 11, 14, 9, 0)) == slot
    assert nas.due(GOOD, {}, datetime(2026, 11, 14, 16, 0)) is None
    assert nas.due(dict(GOOD, enabled=False), {}, at) is None


def test_due_handles_a_late_evening_time_after_midnight():
    late = dict(GOOD, time="23:30")
    assert nas.due(late, {}, datetime(2026, 11, 15, 1, 0)) == "2026-11-14 23:30"


def test_failed_run_retries_after_an_hour():
    at = datetime(2026, 11, 14, 3, 0)
    status = {"attempt_slot": "2026-11-14 03:00", "next_retry": at.timestamp() + 3600}
    assert nas.due(GOOD, status, at) is None
    assert nas.due(GOOD, status, datetime(2026, 11, 14, 4, 1)) == "2026-11-14 03:00"


def test_record_result_marks_slot_done_or_schedules_retry(tmp_path):
    s = nas.record_result(tmp_path, False, "NAS off", 0, "2026-11-14 03:00")
    assert s["ok"] is False and "done_slot" not in s and s["next_retry"] > s["last_attempt"]
    s = nas.record_result(tmp_path, True, "Saved", 123, "2026-11-14 03:00")
    assert s["ok"] and s["done_slot"] == "2026-11-14 03:00" and s["last_bytes"] == 123


def test_prune_keeps_newest_and_never_touches_other_folders(tmp_path):
    for name in ["2026-11-10_030000", "2026-11-11_030000", "2026-11-12_030000", "2026-11-13_030000"]:
        (tmp_path / name).mkdir()
    (tmp_path / "2026-11-09_030000.partial").mkdir()
    (tmp_path / "my photos").mkdir()
    (tmp_path / "2026-11-01").mkdir()
    removed = nas.prune(tmp_path, 2)
    assert sorted(removed) == ["2026-11-09_030000.partial", "2026-11-10_030000", "2026-11-11_030000"]
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "2026-11-01",
        "2026-11-12_030000",
        "2026-11-13_030000",
        "my photos",
    ]


def test_mount_errors_are_explained_in_plain_english():
    assert "login" in nas._explain_mount_error("mount error(13): Permission denied", "nas")
    assert "share name" in nas._explain_mount_error("mount error(2): No such file or directory", "nas")
    assert "switched on" in nas._explain_mount_error("mount error(112): Host is down", "nas")


def _fake_mount(tmp_path):
    return (
        patch.object(nas, "MOUNT_POINT", tmp_path),
        patch.object(nas, "mount", return_value=(True, "")),
        patch.object(nas, "unmount"),
    )


def test_run_backup_writes_a_dated_folder_and_prunes(tmp_path):
    p1, p2, p3 = _fake_mount(tmp_path)
    with p1, p2, p3 as unmount:
        base = tmp_path / "k4nza"
        base.mkdir()
        for name in ["2026-01-01_030000", "2026-01-02_030000", "2026-01-03_030000"]:
            (base / name).mkdir()

        def dump(path):
            path.write_bytes(b"PGDMP" + b"x" * 100)
            return True, ""

        ok, message, total = nas.run_backup(GOOD, "k4nza", lambda f: f.write(b"zip"), dump)
        assert ok, message
        assert total == 108
        runs = sorted(p.name for p in base.iterdir())
        assert len(runs) == 3 and "2026-01-01_030000" not in runs
        newest = base / runs[-1]
        assert sorted(p.name.split("-")[0] for p in newest.iterdir()) == ["adsb", "skystats"]
        unmount.assert_called()
    assert nas.progress()["running"] is False


def test_run_backup_cleans_up_when_the_database_dump_fails(tmp_path):
    p1, p2, p3 = _fake_mount(tmp_path)
    with p1, p2, p3 as unmount:
        ok, message, _ = nas.run_backup(GOOD, "k4nza", lambda f: f.write(b"zip"), lambda path: (False, "db down"))
        assert not ok and "db down" in message
        assert list((tmp_path / "k4nza").iterdir()) == []
        unmount.assert_called()


def test_run_backup_without_skystats_saves_settings_only(tmp_path):
    p1, p2, p3 = _fake_mount(tmp_path)
    with p1, p2, p3:
        ok, message, _ = nas.run_backup(dict(GOOD, folder="pi5"), "k4nza", lambda f: f.write(b"zip"), None)
        assert ok and "SkyStats is off" in message
        (run,) = (tmp_path / "pi5").iterdir()
        assert [p.suffix for p in run.iterdir()] == [".backup"]


def test_run_backup_reports_an_unreachable_nas(tmp_path):
    with patch.object(nas, "mount", return_value=(False, "Could not reach the NAS")):
        ok, message, _ = nas.run_backup(GOOD, "k4nza", lambda f: None, None)
    assert not ok and "reach" in message
    assert nas.progress()["running"] is False


def test_only_one_backup_at_a_time(tmp_path):
    nas._lock.acquire()
    try:
        assert nas.run_backup(GOOD, "k4nza", lambda f: None, None)[0] is False
        assert nas.test_connection(GOOD, "k4nza")[0] is False
    finally:
        nas._lock.release()


# ---------------------------------------------------------------- the Backup page form


def _post(tmp_path, form):
    from types import SimpleNamespace

    import app as app_module
    from flask import Flask

    flask_app = Flask(__name__)
    flask_app.secret_key = "test"
    flask_app.add_url_rule("/backup", "backup", lambda: "")
    fake = SimpleNamespace(_d=SimpleNamespace(config_path=tmp_path), _nas_site_name=lambda: "k4nza")
    with flask_app.test_request_context("/k4nza/nas-backup", method="POST", data=form):
        resp = app_module.AdsbIm.k4nza_nas_backup_post(fake)
        from flask import get_flashed_messages

        return resp, get_flashed_messages()


def _form(**change):
    form = {
        "nas_enabled": "on",
        "nas_host": GOOD["host"],
        "nas_share": GOOD["share"],
        "nas_folder": "",
        "nas_user": GOOD["user"],
        "nas_password": GOOD["password"],
        "nas_time": "03:00",
        "nas_keep": "3",
        "action": "save",
    }
    form.update(change)
    return {k: v for k, v in form.items() if v is not None}


def test_page_save_and_keep_password_when_left_empty(tmp_path):
    resp, messages = _post(tmp_path, _form())
    assert resp.status_code == 302 and resp.location.endswith("/backup#nas")
    assert nas.load_settings(tmp_path) == GOOD
    assert "every night at 03:00" in messages[0]
    _post(tmp_path, _form(nas_password="", nas_keep="7"))
    saved = nas.load_settings(tmp_path)
    assert saved["password"] == GOOD["password"] and saved["keep"] == 7


def test_page_typo_never_overwrites_working_settings(tmp_path):
    nas.save_settings(tmp_path, GOOD)
    _, messages = _post(tmp_path, _form(nas_host="", nas_password=""))
    assert nas.load_settings(tmp_path) == GOOD
    assert any("NAS address" in m for m in messages)


def test_page_test_button_does_not_switch_backup_on(tmp_path):
    with patch.object(nas, "test_connection", return_value=(True, "Connected")):
        _, messages = _post(tmp_path, _form(action="test"))
    assert messages == ["✓ Connected"]
    saved = nas.load_settings(tmp_path)
    assert saved["enabled"] is False and saved["host"] == GOOD["host"]


def test_page_first_save_waits_for_the_chosen_time(tmp_path):
    with patch.object(nas, "current_slot", return_value="2026-11-14 03:00"):
        _post(tmp_path, _form())
    assert nas.load_status(tmp_path)["done_slot"] == "2026-11-14 03:00"
