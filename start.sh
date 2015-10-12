#! /usr/bin/env bash
python virtualenv/bin/gunicorn --access-logfile - -b 127.0.0.1:9000 -w 1 -t 0 'fibpro.fibpro:app'
