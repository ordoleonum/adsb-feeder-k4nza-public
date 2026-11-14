#!/bin/bash

# default log size limit for every container (Docker's default has no limit
# and the logs live on the SD card). Takes effect the next time Docker starts.
k4nza_docker_log_limits() {
    local f=/etc/docker/daemon.json tmp
    mkdir -p /etc/docker
    [[ -s "$f" ]] || echo '{}' > "$f"
    if [[ $(jq -r 'has("log-opts")' "$f" 2>/dev/null) != "true" ]]; then
        tmp=$(mktemp)
        if jq '. + {"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' "$f" > "$tmp"; then
            mv "$tmp" "$f"
        else
            rm -f "$tmp"
        fi
    fi
}

k4nza_docker_log_limits
