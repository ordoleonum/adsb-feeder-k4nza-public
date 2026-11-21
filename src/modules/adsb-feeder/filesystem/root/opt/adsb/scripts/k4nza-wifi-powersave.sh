#!/bin/bash
# K4NZA: turn WiFi power saving off. With it on, the Pi's WiFi naps between
# packets, which adds delay spikes (100+ ms) and slows everything reached over
# WiFi (map, alert screenshots, feeding). Costs well under 1 W.
# Run from the image build and from every feeder update; safe to run again.

conf_dir=/etc/NetworkManager/conf.d
[[ -d /etc/NetworkManager ]] || exit 0
mkdir -p "$conf_dir"
cat > "$conf_dir/k4nza-wifi-powersave.conf" << 'CONF'
# K4NZA: WiFi power saving off (2 = disable), for all WiFi connections
[connection]
wifi.powersave = 2
CONF

# also switch it off right now on a running system (no reconnect needed)
if command -v iw &> /dev/null; then
    for dev in $(iw dev 2> /dev/null | awk '/Interface/ {print $2}'); do
        iw dev "$dev" set power_save off 2> /dev/null && echo "WiFi power saving off on $dev"
    done
fi
exit 0
