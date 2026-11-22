"""Tests for the cross-site check and the post-login redirect."""

import pytest
from utils.k4nza_csrf import is_cross_site, safe_next


def post(host, origin=None, referer=None, site=None, forwarded=(), scheme="http", path="/update"):
    return is_cross_site("POST", path, host, origin, referer, site, forwarded, scheme)


@pytest.mark.parametrize(
    "host, origin",
    [
        ("adsb-feeder.local", "http://adsb-feeder.local"),
        ("k4nza-adsb.local", "http://k4nza-adsb.local"),
        ("192.168.1.40", "http://192.168.1.40"),
        ("192.168.1.40:80", "http://192.168.1.40"),  # explicit default port in Host
        ("100.101.102.103", "http://100.101.102.103"),  # Tailscale IP
        ("k4nza-adsb.tail1234.ts.net", "http://k4nza-adsb.tail1234.ts.net"),  # MagicDNS
        ("[fe80::1]", "http://[fe80::1]"),
        ("ADSB-Feeder.local", "http://adsb-feeder.local"),
    ],
)
def test_own_pages_are_accepted_at_any_address(host, origin):
    assert not post(host, origin=origin, site="same-origin")


def test_other_websites_are_refused():
    assert post("adsb-feeder.local", origin="https://evil.example", site="cross-site")
    # even without Sec-Fetch-Site (older browsers) the Origin decides
    assert post("adsb-feeder.local", origin="https://evil.example")
    assert post("adsb-feeder.local", origin="null")
    # same host, other port (e.g. something on :8080) is not the feeder's page
    assert post("adsb-feeder.local", origin="http://adsb-feeder.local:8080")


def test_referer_is_used_when_origin_is_missing():
    assert not post("adsb-feeder.local", referer="http://adsb-feeder.local/advanced")
    assert post("adsb-feeder.local", referer="http://evil.example/page")


def test_clients_without_browser_headers_still_work():
    # curl or scripts on the Pi send neither header
    assert not post("127.0.0.1")


def test_proxy_that_rewrites_host_is_accepted_through_forwarded_host():
    # e.g. Tailscale Serve: browser at https://name.ts.net, app sees Host 127.0.0.1
    assert not post("127.0.0.1", origin="https://k4nza-adsb.tail1234.ts.net", forwarded=["k4nza-adsb.tail1234.ts.net"])
    assert post("127.0.0.1", origin="https://k4nza-adsb.tail1234.ts.net")


def test_https_default_port():
    assert not post("feeder.example:443", origin="https://feeder.example", scheme="https")


def test_plain_page_loads_are_never_refused():
    assert not is_cross_site("GET", "/advanced", "adsb-feeder.local", None, None, "cross-site")
    assert not is_cross_site("GET", "/api/k4nza/home", "adsb-feeder.local", "https://evil.example", None, "cross-site")


def test_risky_links_from_other_sites_are_refused():
    assert is_cross_site("GET", "/feeder-update-stable", "adsb-feeder.local", None, None, "cross-site")
    assert is_cross_site("GET", "/change_sdr_serial/1/2", "adsb-feeder.local", None, None, "cross-site")
    # typed in or bookmarked: browsers send "none"; from the feeder itself: same-origin
    assert not is_cross_site("GET", "/feeder-update-stable", "adsb-feeder.local", None, None, "none")
    assert not is_cross_site("GET", "/change_sdr_serial/1/2", "adsb-feeder.local", None, None, "same-origin")


@pytest.mark.parametrize(
    "target, expected",
    [
        ("/advanced", "/advanced"),
        ("/systemmgmt?m=1", "/systemmgmt?m=1"),
        ("//evil.example", ""),
        ("/\\evil.example", ""),
        ("http://evil.example/", ""),
        ("http://localhost/advanced", ""),
        ("javascript:alert(1)", ""),
        ("/a\r\nLocation: x", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_safe_next(target, expected):
    assert safe_next(target) == expected


def test_tls_proxy_that_keeps_the_host():
    # Tailscale Serve keeping the Host header: browser uses https, the app sees plain http
    assert not post("k4nza-adsb.tail1234.ts.net", origin="https://k4nza-adsb.tail1234.ts.net")


# ---------------------------------------------------------------- in the app


@pytest.fixture
def client(tmp_path):
    from unittest.mock import MagicMock, patch

    import app as app_module

    with patch("app.Data") as data_cls, patch("app.System"), patch("app.RouteManager"):
        data = MagicMock()
        data.env_by_tags.return_value = MagicMock(valuestr="1.0.0")
        data.version_file = str(tmp_path / "version")
        data.proxy_routes = []
        data_cls.return_value = data
        adsb_im = app_module.AdsbIm()
        adsb_im.app.config["TESTING"] = True
        yield adsb_im, adsb_im.app.test_client()


def test_app_refuses_a_form_from_another_website(client):
    _, c = client
    r = c.post("/update", data={"ssh_pub": "ssh-ed25519 AAAA attacker"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = c.post("/api/mark_changelog_seen", headers={"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403
    r = c.get("/feeder-update-stable", headers={"Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403


def test_app_accepts_its_own_pages(client):
    _, c = client
    r = c.post(
        "/api/mark_changelog_seen",
        base_url="http://100.101.102.103",
        headers={"Origin": "http://100.101.102.103", "Sec-Fetch-Site": "same-origin"},
    )
    assert r.status_code == 200


def test_login_sends_you_back_to_the_page_you_wanted(client):
    adsb_im, c = client
    adsb_im._auth._enabled_func = lambda: True
    r = c.get("/advanced?m=1", base_url="http://adsb-feeder.local")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/login?next=/advanced?m%3D1") or "next=%2Fadvanced" in r.headers["Location"]
    adsb_im._auth.verify_password = lambda u, p: True
    origin = {"Origin": "http://adsb-feeder.local"}
    r = c.post("/login", base_url="http://adsb-feeder.local", data={"next": "/advanced?m=1"}, headers=origin)
    assert r.headers["Location"].endswith("/advanced?m=1")
    r = c.post("/login", base_url="http://adsb-feeder.local", data={"next": "//evil.example"}, headers=origin)
    assert "evil.example" not in r.headers["Location"]


def test_sending_logs_needs_the_login_when_one_is_set(client):
    adsb_im, c = client
    adsb_im._auth._enabled_func = lambda: True
    origin = {"Origin": "http://adsb-feeder.local"}
    r = c.post("/support", base_url="http://adsb-feeder.local", data={"upload": "local_download"}, headers=origin)
    assert r.status_code == 302 and "/login" in r.headers["Location"]
