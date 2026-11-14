#!/bin/bash
# apply WiFi settings from k4nza-wifi.txt on the boot partition.
#
# The boot partition is FAT, so it can be edited from Windows right after
# flashing. Runs on every boot before the hotspot check; does nothing unless
# SSID is filled in. After applying, the SSID/PASSWORD values are cleared from
# the file so the password isn't left on the card.

set -u

FILE=""
for f in /boot/firmware/k4nza-wifi.txt /boot/k4nza-wifi.txt; do
    if [[ -f "$f" ]]; then
        FILE="$f"
        break
    fi
done
[[ -n "$FILE" ]] || exit 0

# read KEY=value (tolerates Windows line endings, a UTF-8 BOM and spaces around '=')
getval() {
    sed -e '1s/^\xEF\xBB\xBF//' -e 's/\r$//' "$FILE" |
        grep -E "^[[:space:]]*$1[[:space:]]*=" | tail -1 |
        sed -E "s/^[[:space:]]*$1[[:space:]]*=//" |
        sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

SSID=$(getval SSID)
PSK=$(getval PASSWORD)
COUNTRY=$(getval COUNTRY | tr '[:lower:]' '[:upper:]')
[[ "$COUNTRY" =~ ^[A-Z]{2}$ ]] || COUNTRY=US

if [[ -z "$SSID" ]]; then
    exit 0
fi

echo "k4nza-wifi: applying WiFi settings for SSID '$SSID' (country $COUNTRY) from $FILE"

if ! command -v nmcli &> /dev/null; then
    echo "k4nza-wifi: NetworkManager (nmcli) not available, cannot configure WiFi"
    exit 0
fi

# make sure the radio is allowed to transmit
rfkill unblock wifi &> /dev/null || true
iw reg set "$COUNTRY" &> /dev/null || true
if command -v raspi-config &> /dev/null; then
    raspi-config nonint do_wifi_country "$COUNTRY" &> /dev/null || true
fi
nmcli radio wifi on &> /dev/null || true

wlan=$(iw dev 2> /dev/null | awk '/Interface/ {print $2; exit}')
[[ -n "$wlan" ]] || wlan=wlan0

# replace any profile we created before
nmcli connection delete k4nza-wifi &> /dev/null || true

if [[ -n "$PSK" ]]; then
    if (( ${#PSK} < 8 || ${#PSK} > 63 )); then
        echo "k4nza-wifi: WARNING - WiFi passwords are normally 8-63 characters; trying anyway"
    fi
    nmcli connection add type wifi ifname "$wlan" con-name k4nza-wifi ssid "$SSID" \
        connection.autoconnect yes connection.autoconnect-priority 50 \
        wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" > /dev/null
else
    nmcli connection add type wifi ifname "$wlan" con-name k4nza-wifi ssid "$SSID" \
        connection.autoconnect yes connection.autoconnect-priority 50 > /dev/null
fi
rc=$?

if (( rc != 0 )); then
    echo "k4nza-wifi: failed to create the WiFi profile (nmcli exit $rc); leaving the file unchanged"
    exit 0
fi

# try to connect now (the network may take a moment to appear in scans)
for i in 1 2 3 4 5 6; do
    if nmcli connection up k4nza-wifi &> /dev/null; then
        echo "k4nza-wifi: connected to '$SSID'"
        break
    fi
    nmcli device wifi rescan &> /dev/null || true
    sleep 5
done

# clear the values from the card; keep the template so it can be reused
tmp="${FILE}.tmp"
sed -e '1s/^\xEF\xBB\xBF//' -e 's/\r$//' "$FILE" |
    sed -E 's/^([[:space:]]*SSID[[:space:]]*=).*/\1/; s/^([[:space:]]*PASSWORD[[:space:]]*=).*/\1/' > "$tmp"
printf '\n# Last applied: %s (SSID "%s") - password erased from this file.\n' "$(date)" "$SSID" >> "$tmp"
sed -i 's/$/\r/' "$tmp"   # keep Windows line endings so Notepad shows it nicely
mv -f "$tmp" "$FILE"
sync

echo "k4nza-wifi: WiFi profile saved; values cleared from $FILE"
exit 0
