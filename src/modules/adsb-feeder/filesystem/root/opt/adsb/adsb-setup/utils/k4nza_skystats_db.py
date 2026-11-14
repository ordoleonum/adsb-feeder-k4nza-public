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
import time
from pathlib import Path

DB_CONTAINER = "skystats-db"
APP_CONTAINER = "skystats"
CHUNK = 1024 * 1024


def _psql(user, password, dbname, sql, timeout=120):
    return subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={password}",
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
    )


def db_container_running():
    r = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", DB_CONTAINER], capture_output=True, text=True, check=False
    )
    return r.returncode == 0 and r.stdout.strip() == "true"


def stream_dump(user, password, dbname):
    """Generator yielding a compressed custom-format pg_dump."""
    proc = subprocess.Popen(
        [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={password}",
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
        stderr=subprocess.DEVNULL,
    )
    assert proc.stdout is not None
    try:
        while True:
            chunk = proc.stdout.read(CHUNK)
            if not chunk:
                break
            yield chunk
    finally:
        proc.stdout.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


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
            ["docker", "exec", "-i", "-e", f"PGPASSWORD={password}", DB_CONTAINER] + cmd,
            stdin=f,
            capture_output=True,
            timeout=4 * 3600,
            check=False,
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
