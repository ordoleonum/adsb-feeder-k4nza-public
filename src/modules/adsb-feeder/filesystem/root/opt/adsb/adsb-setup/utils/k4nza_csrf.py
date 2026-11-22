"""Refuse changes that another website sends through the visitor's browser.

The web interface has no login by default, so without this check any page
opened on the home network could submit a form to the feeder (for example to
add an SSH key). Browsers say where a request comes from (Origin / Referer,
Sec-Fetch-Site); a change is accepted only when that is the very address the
feeder was opened with. No address list is needed, so the LAN IP, .local
names, Tailscale, ZeroTier or NetBird all keep working.
"""

import re
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlsplit

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

# GET links that change something: refused when another website triggers them
# (a bookmark or typing the address still works: browsers send "none" then)
RISKY_GET_PREFIXES = ("/change_sdr_serial/", "/feeder-update-")


def _netloc(value: str, default_scheme: str = "http") -> str:
    """'http://Host:80' -> 'host'; 'https://x:443' -> 'x'; other ports are kept."""
    try:
        parts = urlsplit(value if "//" in value else f"{default_scheme}://{value}")
        host = (parts.hostname or "").lower()
        port = parts.port
    except ValueError:
        return ""
    if not host:
        return ""
    if ":" in host:  # IPv6
        host = f"[{host}]"
    scheme = parts.scheme or default_scheme
    if port is None or (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        return host
    return f"{host}:{port}"


def _own_addresses(host: str, forwarded_hosts: Iterable[str], scheme: str) -> set:
    own = set()
    for h in [host, *forwarded_hosts]:
        for one in (h or "").split(","):
            one = one.strip()
            if one:
                # the Host header has no scheme: accept it with either default port
                own.add(_netloc(one, scheme))
                own.add(_netloc(one, "https" if scheme == "http" else "http"))
    own.discard("")
    return own


def is_cross_site(
    method: str,
    path: str,
    host: str,
    origin: Optional[str],
    referer: Optional[str],
    sec_fetch_site: Optional[str],
    forwarded_hosts: Iterable[str] = (),
    scheme: str = "http",
    risky_get_prefixes: tuple = RISKY_GET_PREFIXES,
) -> bool:
    """True when the request was sent by a page from another address."""
    method = (method or "GET").upper()
    if method in SAFE_METHODS:
        return path.startswith(risky_get_prefixes) and sec_fetch_site == "cross-site"
    if sec_fetch_site == "cross-site":
        return True
    source = origin or referer
    if not source:
        # not a browser (curl, scripts on the Pi): browsers always send Origin
        # on a form post from another site
        return False
    if source.strip() == "null":
        # sandboxed or privacy-stripped pages; the feeder's own pages never send it
        return True
    return _netloc(source) not in _own_addresses(host, forwarded_hosts, scheme)


_SECRET_FIELD = re.compile(r"password|passwd|secret|token|(?:^|[-_])key(?:$|[-_])|ssh_pub", re.IGNORECASE)


def is_secret_field(name: str) -> bool:
    """Form fields whose value must not be written to the log."""
    return bool(_SECRET_FIELD.search(name or ""))


LOGIN_KEY_RESET_MARK = "k4nza-login-key-reset-35"


def login_key_reset_due(config_dir) -> bool:
    """True until the one-time login key renewal of v3.0.15-35 has been done."""
    try:
        return not (Path(config_dir) / LOGIN_KEY_RESET_MARK).exists()
    except (TypeError, OSError):
        return False  # no usable config folder: leave the key alone


def mark_login_key_reset(config_dir) -> None:
    try:
        (Path(config_dir) / LOGIN_KEY_RESET_MARK).write_text("login key renewed after the v3.0.15-35 update\n")
    except OSError:
        pass  # renewed again at the next start: only means logging in once more


def safe_next(target: Optional[str]) -> str:
    """Where to go after logging in: only a path on this feeder, else ''."""
    t = (target or "").strip()
    if not t.startswith("/") or t.startswith("//") or t.startswith("/\\") or "\\" in t:
        return ""
    if any(ord(c) < 32 for c in t):
        return ""
    return t
