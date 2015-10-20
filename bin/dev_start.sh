#! /usr/bin/env bash

function kill_by_pid() {
    for i in `ls etc/dev_*.pid`; do echo "killing $i"; kill -TERM `cat $i`; rm $i; done
}
. "${DIR}/../virtualenv/bin/activate"
DIR=`dirname $0`
SCREENRC="${DIR}/../etc/dev_screen.rc"
# run servers
kill_by_pid
screen -c $SCREENRC
kill_by_pid
