#!/usr/bin/env bash

workdir=`dirname $0`
haproxy_port=8000
haproxy_pid_file="$workdir/../etc/haproxy.pid"

if [[ $1 == run_service ]]; then
    echo "Running local router haproxy on localhost:$haproxy_port"
    haproxy_flags='-db -d'

    if [[ -f $haproxy_pid_file ]]; then
        pid="$(cat "$haproxy_pid_file")"
        cmd="$(basename $(ps -p "$pid" -o comm | tail -n 1))"

        if [[ $cmd == haproxy ]]; then
            echo "Found a running HAProxy instance with PID $pid, killing..."
            kill -TERM "$pid"
        fi

        rm "$haproxy_pid_file"
    fi

    set -m
    haproxy $haproxy_flags -f ${haproxy_config_file:-"${workdir}/../etc/haproxy.conf"} &

    pid="$!"
    echo "$pid" > "$haproxy_pid_file"
    fg
fi
