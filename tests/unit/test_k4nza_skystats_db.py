"""Tests for the streamed SkyStats database download."""

import io
from unittest.mock import patch

import pytest
from utils import k4nza_skystats_db as db


class _Proc:
    def __init__(self, data, code, err=b""):
        self.stdout = io.BytesIO(data)
        self.returncode = code
        self._err = err
        self.stderr_file = None

    def wait(self, timeout=None):
        if self.stderr_file is not None:
            self.stderr_file.write(self._err)
        return self.returncode

    def kill(self):
        pass


def _run(proc):
    calls = {}

    def fake_popen(cmd, stdout=None, stderr=None, env=None):
        calls.update(cmd=cmd, env=env)
        proc.stderr_file = stderr
        return proc

    with patch.object(db.subprocess, "Popen", side_effect=fake_popen):
        return calls, b"".join(db.stream_dump("user", "s3cret", "skystats_db"))


def test_a_good_dump_streams_everything():
    calls, data = _run(_Proc(b"PGDMP" + b"x" * 3000000, 0))
    assert data.startswith(b"PGDMP") and len(data) == 3000005


def test_the_password_is_not_on_the_command_line():
    calls, _ = _run(_Proc(b"PGDMP", 0))
    assert not any("s3cret" in part for part in calls["cmd"])
    assert "PGPASSWORD" in calls["cmd"]
    assert calls["env"]["PGPASSWORD"] == "s3cret"


def test_a_failed_dump_raises_so_the_download_is_cut_off():
    with pytest.raises(db.DumpFailed, match="connection lost"):
        _run(_Proc(b"PGDMP" + b"x" * 10, 1, b"pg_dump: error: connection lost\n"))
