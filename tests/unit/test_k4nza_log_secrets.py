"""Shared diagnostics and the setup log must not contain passwords, keys or the login secret."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from utils.k4nza_csrf import is_secret_field

ADSB = Path(__file__).resolve().parents[2] / "src/modules/adsb-feeder/filesystem/root/opt/adsb"


def _sanitize(tmp_path, config, text):
    src = (ADSB / "scripts/search-replace.py").read_text()
    (tmp_path / "config.json").write_text(json.dumps(config))
    script = tmp_path / "sr.py"
    script.write_text(src.replace("/opt/adsb/config/config.json", (tmp_path / "config.json").as_posix()))
    r = subprocess.run([sys.executable, str(script)], input=text, capture_output=True, text=True, check=True)
    return r.stdout


SECRETS = {
    "SKYSTATS_DB_PASSWORD": "DbPw1234",
    "_ADSBIM_APP_SECRET": "deadbeefsecret",
    "_ADSBIM_WEB_AUTH_PASSWORD_HASH": "scrypt:32768:8:1$salt$hashvalue",
    "SONDE_WEB_PASSWORD": "SondePw9",
    "AISCATCHER_FEEDER_KEY": ["AisKey77"],
    "AIS_APRSFI_FEEDER_KEY": ["AprsKey8"],
}


def test_every_secret_setting_is_hidden(tmp_path):
    config = dict(SECRETS, FEEDER_LAT="35.1234", MLAT_SITE_NAME="K4NZA")
    text = json.dumps(config, indent=1) + "\n_ADSBIM_WEB_AUTH_PASSWORD_HASH=scrypt:32768:8:1$$salt$$hashvalue\n"
    out = _sanitize(tmp_path, config, text)
    for value in ["DbPw1234", "deadbeefsecret", "hashvalue", "SondePw9", "AisKey77", "AprsKey8", "35.1234"]:
        assert value not in out, value


def test_common_words_are_not_garbled(tmp_path):
    # the radiosonde password defaults to "none": every "none" in the log must not be replaced
    out = _sanitize(tmp_path, {"SONDE_WEB_PASSWORD": "none"}, "container is none of these\n")
    assert out == "container is none of these\n"


def test_a_setting_missing_from_the_config_does_not_stop_the_log(tmp_path):
    assert _sanitize(tmp_path, {}, "hello\n") == "hello\n"


@pytest.mark.skipif(shutil.which("perl") is None, reason="needs perl, as on the Pi")
def test_old_log_lines_with_passwords_are_redacted():
    line = next(ln for ln in (ADSB / "log-sanitizer.sh").read_text().splitlines() if "K4NZA" not in ln and "(handling " in ln)
    expr = re.search(r"replace_args\+='(.*)'", line).group(1)
    text = (
        "x handling wifi_password -> MyWifiPass\n"
        "x handling flightradar--key -> ABC123\n"
        "x handling netbird_setup_key -> NB-1\n"
        "x handling site_name -> K4NZA\n"
        "x handling nas_keep -> 14\n"
    )
    out = subprocess.run(["perl", "-pe", expr], input=text, capture_output=True, text=True, check=True).stdout
    assert "MyWifiPass" not in out and "ABC123" not in out and "NB-1" not in out
    assert "site_name -> K4NZA" in out and "nas_keep -> 14" in out


@pytest.mark.parametrize(
    "name",
    ["wifi_password", "skystats_db_password", "sonde_web_password", "netbird_setup_key", "flightradar--key",
     "aiscatcher_feeder_key", "ssh_pub", "passwd", "password", "nas_password"],
)
def test_secret_form_fields(name):
    assert is_secret_field(name)


@pytest.mark.parametrize("name", ["site_name", "wifi_ssid", "nas_keep", "keep_days", "skystats--is_enabled", "lat", "monkey"])
def test_ordinary_form_fields(name):
    assert not is_secret_field(name)
