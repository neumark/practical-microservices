#!/usr/bin/env bash
virtualenv/bin/python virtualenv/bin/gunicorn -t 0 -b 127.0.0.1:9102 -w 1 -p etc/dev_logsink.pid 'fibpro.logsink:LogSinkServer().app()'

