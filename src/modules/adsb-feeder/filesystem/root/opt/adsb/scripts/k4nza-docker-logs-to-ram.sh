#!/bin/bash
# K4NZA builds up to v3.0.15-23 switched Docker's container logs to files on the
# SD card (json-file, 10 MB x 3 per container). Stock adsb.im logs to journald,
# which is kept in memory once setup is done - no SD card writes. Put that back.
# Only a daemon.json with exactly the K4NZA settings is changed.

f=/etc/docker/daemon.json
[[ -f "$f" ]] || exit 0
[[ $(jq -cS '[."log-driver", ."log-opts"]' "$f" 2> /dev/null) == '["json-file",{"max-file":"3","max-size":"10m"}]' ]] || exit 0

tmp=$(mktemp)
if ! jq '."log-driver" = "journald" | del(."log-opts")' "$f" > "$tmp"; then
    rm -f "$tmp"
    exit 0
fi
echo "container logs: back to memory (journald) instead of files on the SD card"

# containers keep the log setting they were created with: remove them so they
# are recreated with the new one (settings and data live outside the
# containers and are kept)
/opt/adsb/docker-compose-adsb down -t 30 || true
install -m 0644 "$tmp" "$f"
rm -f "$tmp"
systemctl restart docker
