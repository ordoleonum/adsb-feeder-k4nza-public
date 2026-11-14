import os
import subprocess
import time
import traceback

from utils.util import print_err, run_shell_captured


class Wifi:
    def __init__(self, wlan="wlan0"):
        if os.path.exists("/boot/dietpi"):
            self.baseos = "dietpi"
        elif os.path.exists("/etc/rpi-issue"):
            self.baseos = "raspbian"
        else:
            print_err("unknown baseos - no idea what to do")
            self.baseos = "unknown"
        self.wlan = wlan

    def get_ssid(self):
        try:
            # if you aren't on wifi, this will return an empty string
            ssid = subprocess.run(
                "iwgetid -r",
                shell=True,
                capture_output=True,
                timeout=2.0,
            ).stdout.decode("utf-8")
        except Exception:
            ssid = ""

        return ssid.strip()

    def wait_wpa_supplicant(self):
        # wait for wpa_supplicant to be running
        startTime = time.time()
        success = False
        while time.time() - startTime < 45:
            success, output = run_shell_captured("pgrep wpa_supplicant", timeout=5)
            time.sleep(1)
            if success:
                break
        if not success:
            print_err("timeout while waiting for wpa_supplicant to start")
        return success

    def wpa_cli_reconfigure(self):
        connected = False
        output = ""
        proc: subprocess.Popen | None = None

        try:
            proc = subprocess.Popen(
                ["wpa_cli", f"-i{self.wlan}"],
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
            )
            if proc.stdout == None or proc.stdin == None:
                print_err("ERROR: can't start wpa_cli, proc.stdout or proc.stdin is None")
                return False
            os.set_blocking(proc.stdout.fileno(), False)

            startTime = time.time()
            reconfigureSent = False
            reconfigured = False
            while time.time() - startTime < 20:
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.01)
                    continue

                output += line
                # print_err(f"wpa_cli: {line.rstrip()})")
                if not reconfigureSent and line.startswith(">"):
                    proc.stdin.write("reconfigure\n")
                    proc.stdin.flush()
                    reconfigureSent = True
                if "reconfigure" in line:
                    reconfigured = True
                if reconfigured and "CTRL-EVENT-CONNECTED" in line:
                    connected = True
                    break
        except Exception:
            print_err(traceback.format_exc())
        finally:
            if proc:
                proc.terminate()

        if not connected:
            print_err(f"Couldn't connect after wpa_cli reconfigure: ouput: {output}")

        return connected

    def wpa_cli_scan(self):
        ssids: list[str] = []
        output: str = ""
        proc: subprocess.Popen | None = None
        try:
            proc = subprocess.Popen(
                ["wpa_cli", f"-i{self.wlan}"],
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
            )
            if proc.stdout == None or proc.stdin == None:
                print_err("ERROR: can't start wpa_cli, proc.stdout or proc.stdin is None")
                return []
            os.set_blocking(proc.stdout.fileno(), False)

            startTime = time.time()
            while time.time() - startTime < 15:
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.01)
                    continue

                output += line
                # print(line, end="")
                if line.count("Interactive mode"):
                    proc.stdin.write("scan\n")
                    proc.stdin.flush()
                if line.count("CTRL-EVENT-SCAN-RESULTS"):
                    proc.stdin.write("scan_results\n")
                    proc.stdin.flush()
                    break

            startTime = time.time()
            while time.time() - startTime < 1:
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.01)
                    continue

                output += line
                if line.count("\t"):
                    fields = line.rstrip("\n").split("\t")
                    if len(fields) == 5:
                        ssids.append(fields[4])

        except Exception:
            print_err(f"ERROR in wpa_cli_scan(), wpa_cli ouput: {output}")
        finally:
            if proc:
                proc.terminate()

        return ssids

    def writeWpaConf(self, ssid: str = "", passwd: str = "", path: str = "", country_code: str = "GB"):
        netblocks: dict[str, str] = {}
        netblock: str = ""
        exist_ssid: str | None = None
        try:
            # extract the existing network blocks from the config file
            with open(path, "r") as conf:
                lines = conf.readlines()
                inBlock = False
                for line in lines:
                    if line.strip().startswith("network="):
                        if inBlock:
                            raise SyntaxError("nested network block")
                        netblock = ""
                        exist_ssid = None
                        inBlock = True
                    if inBlock:
                        if "ssid" in line:
                            exist_ssid = line.split('"')[1]
                        if "priority" in line:
                            p1, p2 = line.split("=")
                            # lower priority of all existing networks by 1
                            # negative priorities are allowed so this is fine
                            line = p1 + f"={int(p2) - 1}"
                        netblock += line.rstrip() + "\n"
                    if "}" in line:
                        if not inBlock or not exist_ssid:
                            raise SyntaxError("unexpected close of network block")
                        inBlock = False
                        netblocks[exist_ssid] = netblock
        except Exception:
            print_err(traceback.format_exc())
            print_err(f"ERROR when parsing existing wpa supplicant config, will DISCARD OLD CONFIG")
            netblocks = {}

        try:
            output = subprocess.run(
                ["wpa_passphrase", f"{ssid}", f"{passwd}"],
                capture_output=True,
                check=True,
            ).stdout.decode()
            netblocks[ssid] = output.replace("}", "\tpriority=1000\n}")

            with open(path, "w") as conf:
                conf.write(f"""
# WiFi country code, set here in case the access point does not send one
country={country_code}
# Grant all members of group "netdev" permissions to configure WiFi, e.g. via wpa_cli or wpa_gui
ctrl_interface=DIR=/run/wpa_supplicant GROUP=netdev
# Allow wpa_cli/wpa_gui to overwrite this config file
update_config=1
# disable p2p as it can cause errors
p2p_disabled=1
# enable protected managment frame support
pmf=1
""")
                for k in netblocks.keys():
                    conf.write(netblocks[k])
        except Exception:
            print_err(traceback.format_exc())
            print_err(f"ERROR when writing wpa supplicant config to {path}")
            return False
        print_err("wpa supplicant config written to " + path)
        return True

    def restart_networking_noblock(self):
        res, out = run_shell_captured("systemctl restart --no-block networking.service", timeout=5)

    def dietpi_add_wifi_hotplug(self):
        # enable dietpi wifi in case it is disabled
        changedInterfaces = False
        with open("/etc/network/interfaces", "r") as current, open("/etc/network/interfaces.new", "w") as update:
            lines = current.readlines()
            for line in lines:
                if line.startswith("#") and "allow-hotplug" in line and self.wlan in line:
                    changedInterfaces = True
                    update.write(f"allow-hotplug {self.wlan}\n")
                else:
                    update.write(f"{line}")

        if changedInterfaces:
            print_err(f"uncommenting allow-hotplug for {self.wlan}")
            os.rename("/etc/network/interfaces.new", "/etc/network/interfaces")
            self.restart_networking_noblock()
        else:
            os.remove("/etc/network/interfaces.new")

    def wifi_connect(self, ssid, passwd, country_code="PA"):
        success = False

        if self.baseos == "dietpi":
            self.dietpi_add_wifi_hotplug()

            # wpa_supplicant can take extremely long to start up as long as eth0 has allow-hotplug
            # wpa_cli_reconfigure will wait for that so this test can take up to 60 seconds

            # test wifi
            success = self.writeWpaConf(
                ssid=ssid, passwd=passwd, path="/etc/wpa_supplicant/wpa_supplicant.conf", country_code=country_code
            )
            if success:
                # note to self: don't call ifup from within this
                # stopping adsb-setup service will terminate wpa_supplicant somehow
                if not self.wait_wpa_supplicant():
                    print_err("ERROR: wait_wpa_supplicant didn't work, restarting networking and re-trying")
                    self.restart_networking_noblock()
                    self.wait_wpa_supplicant()

                success = self.wpa_cli_reconfigure()

        elif self.baseos == "raspbian":
            # Wait for NetworkManager and the network to appear, then connect with
            # an explicit WPA2 profile: on WPA2/WPA3 "mixed" routers WPA3 (SAE)
            # often fails with the Pi's WiFi firmware.
            success = self.k4nza_nm_connect(ssid, passwd)
            if success:
                return True
            print_err("k4nza wifi: explicit WPA2 profile failed, falling back to the stock connect method")
            # do a wifi scan to ensure the following connect works
            # this is apparently necessary for NetworkManager
            self.scan_ssids()
            # try for a while because it takes a bit for NetworkManager to come back up
            startTime = time.time()
            while time.time() - startTime < 20:
                try:
                    result = subprocess.run(
                        [
                            "nmcli",
                            "d",
                            "wifi",
                            "connect",
                            f"{ssid}",
                            "password",
                            f"{passwd}",
                            "ifname",
                            f"{self.wlan}",
                        ],
                        capture_output=True,
                        timeout=20.0,
                    )
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    # something went wrong
                    output = ""
                    if e.stdout:
                        output += e.stdout.decode()
                    if e.stderr:
                        output += e.stderr.decode()

                except Exception as e:
                    # catch any other unexpected exceptions
                    print_err(f"run_shell_captured: unexpected exception {e}")
                    output = str(e)

                else:
                    output = result.stdout.decode() + result.stderr.decode()

                success = "successfully activated" in output

                if success:
                    break
                else:
                    # just to safeguard against super fast spin, sleep a bit
                    print_err(f"failed to connect to '{ssid}': {output}")
                    time.sleep(2)
                    continue

        return success

    def _nm(self, args, timeout=30.0):
        """run nmcli, return (returncode, combined output) - never raises"""
        try:
            r = subprocess.run(["nmcli"] + args, capture_output=True, timeout=timeout)
            return r.returncode, (r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")).strip()
        except subprocess.TimeoutExpired:
            return 124, "timeout"
        except Exception as e:
            return 1, str(e)

    def k4nza_nm_connect(self, ssid, passwd):
        # 1. wait until NetworkManager answers (it was just restarted)
        deadline = time.time() + 45
        while time.time() < deadline:
            rc, _ = self._nm(["-t", "-f", "RUNNING", "general"], timeout=5)
            if rc == 0:
                break
            time.sleep(1)
        self._nm(["radio", "wifi", "on"], timeout=10)

        # 2. wait until the network shows up in a scan (scans take a few seconds)
        seen = False
        deadline = time.time() + 45
        while time.time() < deadline:
            self._nm(["device", "wifi", "rescan", "ifname", self.wlan], timeout=15)
            time.sleep(3)
            rc, out = self._nm(["-t", "-f", "SSID", "device", "wifi", "list", "ifname", self.wlan], timeout=15)
            if rc == 0 and ssid in [line.replace("\\:", ":") for line in out.splitlines()]:
                seen = True
                break
        print_err(f"k4nza wifi: '{ssid}' {'found' if seen else 'NOT found'} in scan")

        # 3. explicit profile; WPA2-PSK (works on WPA2 and WPA2/WPA3-mixed routers)
        name = "k4nza-wifi"
        self._nm(["connection", "delete", "id", name], timeout=15)
        cmd = ["connection", "add", "type", "wifi", "ifname", self.wlan, "con-name", name, "ssid", ssid]
        cmd += ["connection.autoconnect", "yes", "connection.autoconnect-priority", "50"]
        if passwd:
            cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", passwd]
        rc, out = self._nm(cmd, timeout=20)
        if rc != 0:
            print_err(f"k4nza wifi: could not create profile: {out}")
            return False
        for attempt in range(3):
            rc, out = self._nm(["--wait", "40", "connection", "up", "id", name], timeout=50)
            if rc == 0:
                print_err(f"k4nza wifi: connected to '{ssid}'")
                return True
            print_err(f"k4nza wifi: attempt {attempt + 1} to connect to '{ssid}' failed: {out}")
            time.sleep(3)
        # leave no broken profile behind (the fallback creates its own)
        self._nm(["connection", "delete", "id", name], timeout=15)
        return False

    def scan_ssids(self):
        ssids = []
        try:
            if self.baseos == "raspbian":
                try:
                    output = subprocess.run(
                        "nmcli --terse --fields SSID dev wifi",
                        shell=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError as e:
                    print_err(f"error scanning for SSIDs: {e}")
                    return

                for line in output.stdout.decode().split("\n"):
                    if line and line != "--" and line not in ssids:
                        ssids.append(line)
            elif self.baseos == "dietpi":
                ssids = self.wpa_cli_scan()

            if len(ssids) > 0:
                print_err(f"found SSIDs: {ssids}")
                self.ssids = ssids
            else:
                print_err("no SSIDs found")

        except Exception as e:
            print_err(f"ERROR in scan_ssids(): {e}")
