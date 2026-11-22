"""SkyStats database backup (streamed) and restore.

Backup
    The dump is streamed straight to the browser in PostgreSQL's compressed
    "custom" format, so even years of history never have to fit in memory.

Restore
    Accepts either a custom-format dump (.dump, from this build) or a plain SQL
    dump (.sql, from stock adsb.im backups). The data is restored into a *new*
    database first; only when that succeeds is it swapped in for the live one.
    If anything fails, the existing data is left untouched.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path

DB_CONTAINER = "skystats-db"
APP_CONTAINER = "skystats"
CHUNK = 1024 * 1024


def _pg_env(password):
    # "docker exec -e PGPASSWORD" (no value) copies it from this environment,
    # so the password never shows up in the process list
    env = dict(os.environ)
    env["PGPASSWORD"] = password or ""
    return env


def _psql(user, password, dbname, sql, timeout=120):
    return subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            "PGPASSWORD",
            DB_CONTAINER,
            "psql",
            "-h",
            "localhost",
            "-U",
            user,
            "-d",
            dbname,
            "-v",
            "ON_ERROR_STOP=1",
            "-q",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=_pg_env(password),
    )


def db_container_running():
    r = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", DB_CONTAINER], capture_output=True, text=True, check=False
    )
    return r.returncode == 0 and r.stdout.strip() == "true"


class DumpFailed(RuntimeError):
    pass


def stream_dump(user, password, dbname):
    """Generator yielding a compressed custom-format pg_dump.

    Raises DumpFailed if pg_dump does not finish cleanly. Once the download has
    started, that cuts the connection without the end-of-download marker, so
    the browser shows the download as failed instead of saving a cut-off file.
    """
    errors = tempfile.TemporaryFile()
    proc = subprocess.Popen(
        [
            "docker",
            "exec",
            "-e",
            "PGPASSWORD",
            DB_CONTAINER,
            "pg_dump",
            "-h",
            "localhost",
            "-U",
            user,
            "-d",
            dbname,
            "--no-owner",
            "--no-privileges",
            "-Fc",
            "-Z",
            "6",
        ],
        stdout=subprocess.PIPE,
        stderr=errors,
        env=_pg_env(password),
    )
    assert proc.stdout is not None
    finished = False
    try:
        while True:
            chunk = proc.stdout.read(CHUNK)
            if not chunk:
                break
            yield chunk
        finished = True
    finally:
        proc.stdout.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    if finished and proc.returncode != 0:
        errors.seek(0)
        last = errors.read().decode(errors="replace").strip().splitlines()[-1:] or [f"exit code {proc.returncode}"]
        errors.close()
        raise DumpFailed(f"pg_dump failed: {last[0]}")
    errors.close()


def dump_to_file(user, password, dbname, path: Path, timeout=4 * 3600):
    """Write a compressed custom-format pg_dump to path. Returns (ok, error)."""
    if not db_container_running():
        return False, "the SkyStats database is not running"
    cmd = ["docker", "exec", "-e", "PGPASSWORD", DB_CONTAINER, "pg_dump", "-h", "localhost"]
    cmd += ["-U", user, "-d", dbname, "--no-owner", "--no-privileges", "-Fc", "-Z", "6"]
    try:
        with open(path, "wb") as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=timeout, check=False, env=_pg_env(password))
    except subprocess.TimeoutExpired:
        return False, "pg_dump took too long"
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace").strip().splitlines()[-1:] or ["pg_dump failed"]
        return False, err[0]
    return True, ""


def restore(upload_path: Path, user, password, dbname, log=print):
    """Restore upload_path into the SkyStats database. Returns (ok, message)."""
    if not db_container_running():
        return False, "The SkyStats database is not running. Enable SkyStats first, then try again."

    with open(upload_path, "rb") as f:
        is_custom = f.read(5) == b"PGDMP"

    tmpdb = f"{dbname}_restore"
    olddb = f"{dbname}_old_{int(time.time())}"

    # 1. fresh, empty target database
    _psql(user, password, "postgres", f'DROP DATABASE IF EXISTS "{tmpdb}"')
    r = _psql(user, password, "postgres", f'CREATE DATABASE "{tmpdb}"')
    if r.returncode != 0:
        return False, f"Could not create a temporary database: {r.stderr.strip()}"

    # 2. load the backup into it
    if is_custom:
        cmd = ["pg_restore", "-h", "localhost", "-U", user, "-d", tmpdb, "--no-owner", "--no-privileges", "--exit-on-error"]
    else:
        cmd = ["psql", "-h", "localhost", "-U", user, "-d", tmpdb, "-q", "-v", "ON_ERROR_STOP=1"]
    log(f"skystats restore: loading {'custom' if is_custom else 'SQL'} dump into {tmpdb}")
    with open(upload_path, "rb") as f:
        r = subprocess.run(
            ["docker", "exec", "-i", "-e", "PGPASSWORD", DB_CONTAINER] + cmd,
            stdin=f,
            capture_output=True,
            timeout=4 * 3600,
            check=False,
            env=_pg_env(password),
        )
    if r.returncode != 0:
        _psql(user, password, "postgres", f'DROP DATABASE IF EXISTS "{tmpdb}"')
        err = r.stderr.decode(errors="replace").strip().splitlines()[-3:]
        return False, "The backup could not be loaded, your existing SkyStats data was not changed. " + " ".join(err)

    # 3. swap it in (SkyStats must be stopped so nothing holds a connection)
    subprocess.run(["docker", "stop", "-t", "30", APP_CONTAINER], capture_output=True, check=False)
    try:
        _psql(
            user,
            password,
            "postgres",
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname IN ('{dbname}', '{tmpdb}') "
            f"AND pid <> pg_backend_pid()",
        )
        r = _psql(user, password, "postgres", f'ALTER DATABASE "{dbname}" RENAME TO "{olddb}"')
        if r.returncode != 0:
            _psql(user, password, "postgres", f'DROP DATABASE IF EXISTS "{tmpdb}"')
            return False, f"Could not swap databases, existing data unchanged: {r.stderr.strip()}"
        r = _psql(user, password, "postgres", f'ALTER DATABASE "{tmpdb}" RENAME TO "{dbname}"')
        if r.returncode != 0:
            # put the original back
            _psql(user, password, "postgres", f'ALTER DATABASE "{olddb}" RENAME TO "{dbname}"')
            return False, f"Could not swap databases, existing data unchanged: {r.stderr.strip()}"
        _psql(user, password, "postgres", f'DROP DATABASE IF EXISTS "{olddb}"', timeout=600)
    finally:
        subprocess.run(["docker", "start", APP_CONTAINER], capture_output=True, check=False)

    return True, "SkyStats data restored. SkyStats is restarting - give it a minute before opening it."


def receive_upload(environ, dest: Path):
    """Parse the multipart upload, writing the file part directly to dest.

    Returns the uploaded file name, or "" if no file was sent."""
    from werkzeug.formparser import parse_form_data

    dest.parent.mkdir(parents=True, exist_ok=True)
    handles = []

    def stream_factory(total_content_length, content_type, filename, content_length=None):
        fh = open(dest, "wb+")
        handles.append(fh)
        return fh

    _, _, files = parse_form_data(environ, stream_factory=stream_factory)
    f = files.get("file")
    name = f.filename if f else ""
    for fh in handles:
        fh.close()
    if not name or not dest.exists() or dest.stat().st_size == 0:
        return ""
    return name


def cleanup(path: Path):
    try:
        os.remove(path)
    except OSError:
        pass
