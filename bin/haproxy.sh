#!/usr/bin/env bash
. "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )/../common.sh"


haproxy_port=8000
haproxy_pid_file="$workdir/haproxy.pid"

register_window "haproxy_$haproxy_port" "$src_config_dir/haproxy.sh run_service"

if [[ $1 == run_service ]]; then
    echo "Running local router haproxy on localhost:$haproxy_port"

    if [ -n "$haproxy_debug" ]; then
        haproxy_flags='-d'
    else
        haproxy_flags='-db'
    fi

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
    haproxy $haproxy_flags -f ${haproxy_config_file:-$src_config_dir/haproxy.conf} &

    pid="$!"
    echo "$pid" > "$haproxy_pid_file"
    fg
fi

if [[ $1 == cleanup ]]; then
    pkill -f 'haproxy.*please/src/config/haproxy.conf'
    rm -f "$haproxy_pid_file"
fi
