import json
from logging import getLogger

log = getLogger('gunicorn.error')

def load_config(config_file=None):
    config = {}
    if config_file is None:
        return config
    if type(config_file) == list:
        file_list = config_file
    else:
        file_list = [config_file]
    for filename in file_list:
        with open(filename, "r") as f:
            config.update(json.loads(f.read()))
    return config

def http_response(start_response, status="200 OK", body=""):
    body_str = str(body)
    start_response(status, [
        ("Content-Type", "text/plain"),
        ("Content-Length", 
            str(len(body_str)))
    ])
    return iter([body_str])
