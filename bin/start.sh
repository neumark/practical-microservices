#! /usr/bin/env bash

DIR=`dirname $0`
SCREENRC="${DIR}/../etc/screen.rc"
# run servers
screen -c $SCREENRC
eval "${DIR}/bin/haproxy.sh cleanup"

#python virtualenv/bin/gunicorn --access-logfile - -b 127.0.0.1:9000 -w 1 -t 0 'fibpro.fibpro:app'
