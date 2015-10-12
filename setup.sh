#!/usr/bin/env bash
virtualenv -p python2.7 virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt
