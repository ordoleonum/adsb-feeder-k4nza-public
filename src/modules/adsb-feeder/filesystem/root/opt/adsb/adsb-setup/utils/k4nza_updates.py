"""One-click feeder updates from the public adsb-feeder-k4nza-public repository,
plus the Raspberry Pi OS update check.

The newest k4nza-v* release on GitHub is compared with the installed version
(/opt/adsb/k4nza.version). No key or account is needed.
"""

import html
import os
import platform
import re
import subprocess
import threading
import time
from pathlib import Path

import requests

from utils.paths import get_adsb_base_dir

REPO = "ordoleonum/adsb-feeder-k4nza-public"
API = f"https://api.github.com/repos/{REPO}"


def _base() -> Path:
    return Path(get_adsb_base_dir())


def installed_version() -> str:
    try:
        v = (_base() / "k4nza.version").read_text().strip()
        return v or "unknown"
    except OSError:
        return "unknown"


_cache: dict = {"t": 0.0, "data": None}


def latest_release(use_cache: bool = True) -> dict:
    """Return {"ok": bool, "tag": str, "published": str, "notes": str, "error": str}."""
    if use_cache and _cache["data"] is not None and time.time() - _cache["t"] < 600:
        return _cache["data"]
    result = {"ok": False, "tag": "", "published": "", "notes": "", "error": ""}
    try:
        r = requests.get(f"{API}/releases/latest", headers={"Accept": "application/vnd.github+json"}, timeout=10)
    except requests.RequestException as e:
        result["error"] = f"Could not reach GitHub ({e.__class__.__name__}). Is the feeder online?"
        return result
    if r.status_code == 404:
        result["error"] = "No K4NZA release has been published yet."
    elif r.status_code == 403:
        result["error"] = "GitHub is busy (rate limit) - try again in a few minutes."
    elif r.status_code != 200:
        result["error"] = f"GitHub answered {r.status_code}."
    else:
        j = r.json()
        result.update(ok=True, tag=j.get("tag_name", ""), published=j.get("published_at", ""), notes=j.get("body", ""))
    _cache["t"] = time.time()
    _cache["data"] = result
    return result


def clear_cache() -> None:
    _cache["data"] = None


TAG_RE = re.compile(r"^k4nza-v[0-9][0-9.]*-[0-9]+$")
FIRST_KEPT_RELEASE = 20  # from k4nza-v3.0.15-20 on, every release tag stays on GitHub


def previous_version() -> str:
    """The release this feeder ran before its last update ('' if none).
    Written by feeder-update; rollback is possible from -20 on."""
    try:
        v = (_base() / "k4nza.version.prev").read_text().strip()
    except OSError:
        return ""
    if not TAG_RE.match(v) or v == installed_version():
        return ""
    # releases before -20 were published without keeping their tags
    if int(v.rsplit("-", 1)[1]) < FIRST_KEPT_RELEASE:
        return ""
    return v


def request_version(tag: str) -> bool:
    """Ask the next feeder-update run to install this release instead of the newest."""
    if not TAG_RE.match(tag):
        return False
    try:
        (_base() / "k4nza-update-target").write_text(tag + "\n")
    except OSError:
        return False
    return True


def status(refresh: bool = False) -> dict:
    installed = installed_version()
    latest = latest_release(use_cache=not refresh)
    return {
        "installed": installed,
        "latest": latest.get("tag", ""),
        "published": latest.get("published", ""),
        "error": latest.get("error", ""),
        "update_available": bool(latest.get("ok")) and latest.get("tag", "") not in ("", installed),
        "notes_html": render_notes(latest.get("notes", "")),
        "previous": previous_version(),
    }


# ---------------------------------------------------------------------------
# Release notes: the release body is that release's CHANGELOG.md section.
# Only a small, safe subset of Markdown is turned into HTML; everything is
# escaped first, so nothing in the notes can inject markup.

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
_CODE_RE = re.compile(r"`([^`]+)`")


def _inline(text: str) -> str:
    text = html.escape(text, quote=True)
    text = _CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    text = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', text)
    return text


def render_notes(md: str, max_lines: int = 80) -> str:
    out = []
    in_list = False
    in_para = False
    for line in (md or "").replace("\r\n", "\n").split("\n")[:max_lines]:
        stripped = line.strip()
        if stripped == "---":
            break  # the install note below this line isn't news
        is_item = stripped.startswith(("- ", "* "))
        if in_list and not is_item and not (stripped and line.startswith("  ")):
            out.append("</ul>")
            in_list = False
        if not stripped:
            in_para = False
            continue
        if is_item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(stripped[2:])}</li>")
        elif in_list:
            # continuation of the previous bullet
            out[-1] = out[-1][: -len("</li>")] + " " + _inline(stripped) + "</li>"
        elif stripped.startswith("#"):
            out.append(f"<h6>{_inline(stripped.lstrip('#').strip())}</h6>")
            in_para = False
            continue
        elif in_para and out and out[-1].startswith("<p>"):
            # a wrapped line of the same paragraph
            out[-1] = out[-1][: -len("</p>")] + " " + _inline(stripped) + "</p>"
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
        in_para = not is_item
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Raspberry Pi OS: what's installed and how many package updates are waiting.
# The check runs `apt-get update` in a background thread (it can take a while
# on a slow link) and is repeated at most every few hours unless asked.

OS_CHECK_MAX_AGE = 6 * 3600

_os: dict = {"t": 0.0, "running": False, "count": None, "packages": [], "error": ""}
_os_lock = threading.Lock()


def os_installed() -> str:
    name = ""
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                name = line.split("=", 1)[1].strip().strip('"')
                break
    except OSError:
        pass
    kernel = platform.release()
    if name and kernel:
        return f"{name}, kernel {kernel}"
    return name or kernel or "unknown"


def _run_os_check() -> None:
    count = None
    packages: list = []
    error = ""
    try:
        upd = subprocess.run(["apt-get", "update", "-qq"], capture_output=True, text=True, timeout=300, env=_apt_env())
        if upd.returncode != 0:
            error = "Could not refresh the package lists (is the feeder online?)."
        # same command scripts/update-os runs, so the list shown is what installs
        sim = subprocess.run(
            ["apt-get", "-s", "-o", "Debug::NoLocking=1", "upgrade"],
            capture_output=True,
            text=True,
            timeout=120,
            env=_apt_env(),
        )
        if sim.returncode == 0:
            packages = [ln.split()[1] for ln in sim.stdout.splitlines() if ln.startswith("Inst ")]
            count = len(packages)
        elif not error:
            error = "Could not work out which updates are waiting."
    except (OSError, subprocess.SubprocessError) as e:
        error = f"Update check failed ({e.__class__.__name__})."
    with _os_lock:
        _os.update(t=time.time(), running=False, count=count, packages=packages, error=error)


def _apt_env() -> dict:
    env = dict(os.environ)
    env["DEBIAN_FRONTEND"] = "noninteractive"
    env["LC_ALL"] = "C"
    return env


def os_check(force: bool = False) -> None:
    """Start a background check unless one is running or a recent result exists."""
    with _os_lock:
        if _os["running"]:
            return
        if not force and _os["t"] and time.time() - _os["t"] < OS_CHECK_MAX_AGE:
            return
        _os["running"] = True
    threading.Thread(target=_run_os_check, name="k4nza-os-check", daemon=True).start()


def os_forget() -> None:
    """Drop the last result (after installing updates the count is stale)."""
    with _os_lock:
        _os.update(t=0.0, count=None, packages=[], error="")


def _kernel_key(release: str) -> tuple:
    nums = []
    for part in release.split("+", 1)[0].replace("-", ".").split("."):
        nums.append(int(part) if part.isdigit() else 0)
    return tuple(nums)


def os_update_running() -> bool:
    """True while the Pi OS update (scripts/update-os) is still running."""
    try:
        r = subprocess.run(["systemctl", "is-active", "adsb-feeder-update-os"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.stdout.strip() in ("active", "activating")


def reboot_needed() -> bool:
    """True when a newer kernel of the running flavour is installed but not booted."""
    if Path("/run/reboot-required").exists():
        return True
    running = platform.release()  # e.g. 6.18.34+rpi-2712
    if "+" not in running:
        return False
    flavour = running.split("+", 1)[1]
    try:
        installed = [p.name for p in Path("/lib/modules").iterdir() if p.name.endswith("+" + flavour)]
    except OSError:
        return False
    if not installed:
        return False
    newest = max(installed, key=_kernel_key)
    return _kernel_key(newest) > _kernel_key(running)


def os_status(start_check: bool = True) -> dict:
    if start_check:
        os_check()
    with _os_lock:
        checked = int(_os["t"])
        return {
            "installed": os_installed(),
            "reboot_needed": reboot_needed(),
            "checking": _os["running"],
            "count": _os["count"],
            "packages": list(_os["packages"][:40]),
            "error": _os["error"],
            "checked": checked,
            "checked_ago": _ago(checked),
        }


def _ago(t: int) -> str:
    if not t:
        return ""
    s = int(time.time()) - t
    if s < 90:
        return "just now"
    if s < 5400:
        return f"{s // 60} minutes ago"
    if s < 172800:
        return f"{s // 3600} hours ago"
    return f"{s // 86400} days ago"
