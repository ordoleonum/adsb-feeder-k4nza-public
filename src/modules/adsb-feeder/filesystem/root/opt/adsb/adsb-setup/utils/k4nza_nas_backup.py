"""Nightly backup to a network share (a NAS) over SMB.

Each run connects to the share, writes one dated folder with the same files the
Backup page offers for download (configuration + graphs zip, and the SkyStats
database when SkyStats is on), deletes the oldest folders beyond the "keep"
count, and disconnects again.

Design rules:
- The share is only mounted while a backup (or a connection test) runs, so a
  NAS that is switched off can never slow down or block the feeder.
- Everything is written straight to the share; nothing extra lands on the SD card.
- Settings live in their own file (mode 0600), not in config.json: the NAS
  password never reaches the docker .env file, the logs, or the backup zip.
- Only folders this code created (YYYY-MM-DD_HHMMSS) are ever deleted.
"""

import json
import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

MOUNT_POINT = Path("/run/k4nza-nas-backup")
CRED_FILE = Path("/run/k4nza-nas-backup.cred")
SETTINGS_NAME = "k4nza-nas-backup.json"
STATUS_NAME = "k4nza-nas-backup-status.json"

RUN_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")
PARTIAL_SUFFIX = ".partial"
RETRY_SECONDS = 3600  # after a failed nightly run, try again an hour later ...
WINDOW_HOURS = 12  # ... for up to 12 hours after the scheduled time

DEFAULTS: Dict[str, Any] = {
    "enabled": False,
    "host": "",
    "share": "",
    "folder": "",
    "user": "",
    "password": "",
    "time": "03:00",
    "keep": 14,
}

_HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,252})$")
_SHARE_RE = re.compile(r"^[^/\\,\x00-\x1f]{1,80}$")
_FOLDER_RE = re.compile(r"^[A-Za-z0-9._ -]{1,64}$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

_lock = threading.Lock()
_progress = {"running": False, "step": "", "started": 0.0}


# ---------------------------------------------------------------- settings / status


def _read_json(path: Path) -> dict:
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, data: dict, mode: int = 0o644) -> None:
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def load_settings(config_dir) -> dict:
    settings = dict(DEFAULTS)
    stored = _read_json(Path(config_dir) / SETTINGS_NAME)
    for key in DEFAULTS:
        if key in stored:
            settings[key] = stored[key]
    try:
        settings["keep"] = int(settings["keep"])
    except (TypeError, ValueError):
        settings["keep"] = DEFAULTS["keep"]
    settings["enabled"] = bool(settings["enabled"])
    return settings


def save_settings(config_dir, settings: dict) -> None:
    clean = {key: settings.get(key, DEFAULTS[key]) for key in DEFAULTS}
    _write_json(Path(config_dir) / SETTINGS_NAME, clean, mode=0o600)


def public_settings(settings: dict) -> dict:
    """Settings safe to show on a page: the password is replaced by a flag."""
    shown = {key: value for key, value in settings.items() if key != "password"}
    shown["has_password"] = bool(settings.get("password"))
    return shown


def load_status(config_dir) -> dict:
    return _read_json(Path(config_dir) / STATUS_NAME)


def save_status(config_dir, status: dict) -> None:
    _write_json(Path(config_dir) / STATUS_NAME, status)


def progress() -> dict:
    return dict(_progress)


def validate(settings: dict) -> list:
    """Return a list of problems (empty when the settings are usable)."""
    errors = []
    if not _HOST_RE.match(settings.get("host", "")):
        errors.append("Enter the NAS address, for example 192.168.1.50 or DS1522.local.")
    if not _SHARE_RE.match(settings.get("share", "")):
        errors.append("Enter the name of the shared folder on the NAS (no slashes or commas).")
    folder = settings.get("folder", "")
    if folder and (not _FOLDER_RE.match(folder) or folder.strip(" .") == ""):
        errors.append("The sub-folder name can only use letters, numbers, spaces, dots, dashes and underscores.")
    user = settings.get("user", "")
    if not user or len(user) > 64 or any(c in user for c in "\r\n,"):
        errors.append("Enter the NAS username.")
    password = settings.get("password", "")
    if not password or any(c in password for c in "\r\n"):
        errors.append("Enter the NAS password.")
    if not _TIME_RE.match(settings.get("time", "")):
        errors.append("Enter the backup time as HH:MM, for example 03:00.")
    try:
        keep = int(settings.get("keep", 0))
    except (TypeError, ValueError):
        keep = 0
    if not 1 <= keep <= 365:
        errors.append("Keep between 1 and 365 backups.")
    return errors


# ---------------------------------------------------------------- scheduling


def due(settings: dict, status: dict, now: datetime) -> Optional[str]:
    """If a scheduled backup should run now, return the key of that night's slot.

    A slot opens at the configured time and stays open for WINDOW_HOURS, so a
    Pi that was off (or a NAS that was asleep) still gets its backup that day.
    A failed attempt is retried every RETRY_SECONDS while the slot is open.
    """
    if not settings.get("enabled"):
        return None
    m = _TIME_RE.match(settings.get("time", ""))
    if not m:
        return None
    slot = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    if now < slot:
        slot -= timedelta(days=1)
    if now - slot > timedelta(hours=WINDOW_HOURS):
        return None
    key = slot.strftime("%Y-%m-%d %H:%M")
    if status.get("done_slot") == key:
        return None
    if status.get("attempt_slot") == key and now.timestamp() < float(status.get("next_retry", 0)):
        return None
    return key


def current_slot(settings: dict, now: datetime) -> Optional[str]:
    """The slot that would be due right now, ignoring what already ran."""
    return due(dict(settings, enabled=True), {}, now)


# ---------------------------------------------------------------- SMB helpers


def _run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def _have_mount_cifs() -> bool:
    return any(Path(p).exists() for p in ("/sbin/mount.cifs", "/usr/sbin/mount.cifs")) or bool(shutil.which("mount.cifs"))


def ensure_cifs(log=print):
    """Make sure the SMB mount helper is installed (one-time apt install)."""
    if _have_mount_cifs():
        return True, ""
    log("nas backup: installing cifs-utils (one time)")
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    cmd = ["apt-get", "install", "-y", "--no-install-recommends", "cifs-utils"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env, check=False)
        if r.returncode != 0:
            subprocess.run(["apt-get", "update"], capture_output=True, timeout=600, env=env, check=False)
            subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env, check=False)
    except Exception as e:
        log(f"nas backup: installing cifs-utils failed: {e}")
    if _have_mount_cifs():
        return True, ""
    return False, "Could not install SMB support (cifs-utils). Check that the feeder has internet access, then try again."


def _explain_mount_error(text: str, host: str) -> str:
    t = text.lower()
    if "permission denied" in t or "error(13)" in t:
        return "The NAS refused the login. Check the username and password, and that this user may use the share."
    if "no such file" in t or "error(2)" in t:
        return "The NAS has no shared folder with that name. Check the share name."
    if "unable to find suitable address" in t or "could not resolve" in t:
        return f"Could not find a NAS at {host}. Check the address (an IP address like 192.168.1.50 is most reliable)."
    if "host is down" in t or "no route" in t or "timed out" in t or "error(112)" in t or "error(113)" in t:
        return f"Could not reach the NAS at {host}. Is it switched on and on the same network?"
    if "connection refused" in t or "error(111)" in t:
        return f"The NAS at {host} is not accepting file sharing connections. Turn on SMB in its File Services."
    last = text.strip().splitlines()[-1] if text.strip() else "unknown error"
    return f"Could not connect to the NAS: {last}"


def mount(settings: dict, log=print):
    ok, message = ensure_cifs(log)
    if not ok:
        return False, message
    unmount()
    MOUNT_POINT.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(CRED_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(f"username={settings['user']}\npassword={settings['password']}\n")
    try:
        r = _run(
            [
                "mount",
                "-t",
                "cifs",
                f"//{settings['host']}/{settings['share']}",
                str(MOUNT_POINT),
                "-o",
                f"credentials={CRED_FILE},uid=0,gid=0,file_mode=0600,dir_mode=0700,soft",
            ],
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, f"Could not reach the NAS at {settings['host']} (no answer within a minute)."
    finally:
        try:
            CRED_FILE.unlink()
        except FileNotFoundError:
            pass
    if r.returncode != 0:
        log(f"nas backup: mount failed: {(r.stderr or r.stdout).strip()}")
        return False, _explain_mount_error((r.stderr or "") + (r.stdout or ""), settings["host"])
    # never write unless the share really is mounted: otherwise the backup
    # would land in /run, which is the Pi's memory
    if not os.path.ismount(MOUNT_POINT):
        log("nas backup: mount reported success but the share is not mounted")
        return False, "Could not connect to the NAS: the share did not stay connected. Try again."
    return True, ""


def unmount():
    if not os.path.ismount(MOUNT_POINT):
        return
    try:
        if _run(["umount", str(MOUNT_POINT)], timeout=30).returncode == 0:
            return
    except subprocess.TimeoutExpired:
        pass
    try:
        _run(["umount", "-l", str(MOUNT_POINT)], timeout=30)
    except subprocess.TimeoutExpired:
        pass


# ---------------------------------------------------------------- backup


def _target_dir(settings: dict, site_name: str) -> Path:
    name = settings.get("folder") or site_name or "adsb-feeder"
    return MOUNT_POINT / name


def prune(base: Path, keep: int) -> list:
    """Delete our oldest backup folders beyond `keep` and any leftover partial ones."""
    removed = []
    runs = sorted(p for p in base.iterdir() if p.is_dir() and RUN_DIR_RE.match(p.name))
    for old in runs[: max(0, len(runs) - keep)]:
        shutil.rmtree(old, ignore_errors=True)
        removed.append(old.name)
    for p in base.iterdir():
        if p.is_dir() and p.name.endswith(PARTIAL_SUFFIX) and RUN_DIR_RE.match(p.name[: -len(PARTIAL_SUFFIX)]):
            shutil.rmtree(p, ignore_errors=True)
            removed.append(p.name)
    return removed


def _human(n: float) -> str:
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def test_connection(settings: dict, site_name: str, log=print):
    """Connect, write and delete a small file, report the free space."""
    if not _lock.acquire(blocking=False):
        return False, "A backup is running right now. Try the test again when it is done."
    try:
        ok, message = mount(settings, log)
        if not ok:
            return False, message
        try:
            base = _target_dir(settings, site_name)
            base.mkdir(exist_ok=True)
            probe = base / ".k4nza-write-test"
            probe.write_text("ok")
            probe.unlink()
            free = shutil.disk_usage(base).free
            return True, f"Connected to the NAS. Backups will go to {settings['share']}/{base.name} ({_human(free)} free)."
        except OSError as e:
            return False, f"Connected, but could not write to the share: {e.strerror or e}"
        finally:
            unmount()
    finally:
        _lock.release()


def run_backup(
    settings: dict,
    site_name: str,
    write_config_zip: Callable,
    dump_skystats: Optional[Callable],
    log=print,
):
    """Run one backup. Returns (ok, message, total_bytes).

    write_config_zip(fileobj) writes the configuration + graphs zip.
    dump_skystats(path) -> (ok, error) writes the SkyStats dump, or is None when SkyStats is off.
    """
    if not _lock.acquire(blocking=False):
        return False, "A backup is already running.", 0
    _progress.update(running=True, step="Connecting to the NAS", started=time.time())
    partial = None
    try:
        ok, message = mount(settings, log)
        if not ok:
            return False, message, 0
        try:
            base = _target_dir(settings, site_name)
            base.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            partial = base / (stamp + PARTIAL_SUFFIX)
            partial.mkdir()

            _progress["step"] = "Saving settings and graphs"
            with open(partial / f"adsb-feeder-config-{site_name}-{stamp}.backup", "wb") as f:
                write_config_zip(f)

            note = ""
            if dump_skystats is not None:
                _progress["step"] = "Saving the SkyStats database"
                ok, error = dump_skystats(partial / f"skystats-db-{site_name}-{stamp}.dump")
                if not ok:
                    return False, f"The SkyStats database could not be saved: {error}", 0
            else:
                note = " SkyStats is off, so only the settings were saved."

            total = sum(p.stat().st_size for p in partial.iterdir() if p.is_file())
            final = base / stamp
            partial.rename(final)
            partial = None

            _progress["step"] = "Removing old backups"
            prune(base, int(settings.get("keep", DEFAULTS["keep"])))
            return True, f"Saved {_human(total)} to {settings['share']}/{base.name}/{final.name}.{note}", total
        except OSError as e:
            return False, f"Writing to the NAS failed: {e.strerror or e}", 0
        finally:
            if partial is not None:
                shutil.rmtree(partial, ignore_errors=True)
            unmount()
    except Exception as e:
        log(f"nas backup: unexpected error: {e}")
        return False, f"The backup failed: {e}", 0
    finally:
        _progress.update(running=False, step="")
        _lock.release()


def record_result(config_dir, ok: bool, message: str, total: int, slot: Optional[str] = None) -> dict:
    """Store the result of a run in the status file and return the new status."""
    status = load_status(config_dir)
    now = time.time()
    status.update(last_attempt=now, ok=ok, message=message)
    if ok:
        status.update(last_ok=now, last_bytes=total)
    if slot:
        status["attempt_slot"] = slot
        if ok:
            status["done_slot"] = slot
        else:
            status["next_retry"] = now + RETRY_SECONDS
    save_status(config_dir, status)
    return status
