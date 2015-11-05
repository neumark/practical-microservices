#!/bin/bash

gunicorn -t 0 -b 127.0.0.1:"$PORT" -w 1 "$MAIN" "$@"
