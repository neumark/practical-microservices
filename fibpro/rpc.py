#!/usr/bin/env python
# dependencies
from raven import Client as RavenClient
from raven.middleware import Sentry
import base64
import json
import requests
import sys
import traceback
from logging import getLogger
# fibpro modules
from const import SENTRY_DSN
from util import (http_response,
    get_default_endpoints, urlsafe_base64_encode,
    urlsafe_base64_decode)

log = getLogger('gunicorn.error')

class RemoteException(Exception):
    pass

class ServerConfig(object):
    def __init__(self):
        self.endpoints = get_default_endpoints()

class RPCBase(object):

    ARG_PREFIX = '?req='
    DEBUG = False

    def encode_data(self, data):
        return json.dumps(
            data,
            separators=(',', ':'),
            sort_keys=True)

    def encode_result(self, result):
        return self.encode_data({
                'result': result
            })

    def encode_exception(self, traceback):
        return self.encode_data({
                'traceback': traceback
            })

    def decode_result(self, response):
        return json.loads(response)

    def encode_arguments(self, method, args):
        return urlsafe_base64_encode(
            self.encode_data(
                {
                    'method': method,
                    'args': args
                }))

    def decode_arguments(self, encoded_data):
        data = json.loads(urlsafe_base64_decode(encoded_data))
        return data['method'], data['args']

class Server(RPCBase):
        
    def ping(self):
        return "pong"

    def wsgi_app(self, environ, start_response):
        method, args = self.decode_arguments(
            environ['QUERY_STRING'][(len(self.ARG_PREFIX)-1):])
        if self.DEBUG:
            log.info('RPC request: %s(**%s)' % (
                method, self.encode_result(args)))
        try:
            body = self.encode_result(
                getattr(self, method)(**args))
        except Exception, e:
            body = self.encode_exception(traceback.format_exc())
        return http_response(start_response,
            body=body)

    def app(self):
        return Sentry(self.wsgi_app,
            RavenClient(SENTRY_DSN))

class Client(RPCBase):

    def __init__(self, server_config=None):
        self.server_config = server_config or ServerConfig()

    def construct_url(self, service, method, args):
        return "%s%s%s" % (
            self.server_config.endpoints[service],
            self.ARG_PREFIX,
            self.encode_arguments(method, args))

    def return_or_raise(self, response):
        if 'result' in response:
            return response['result']
        raise RemoteException(response['traceback'])

    def call(self, service, method, args=None):
        url = self.construct_url(service, method, args or {})
        return self.return_or_raise(
            self.decode_result(requests.get(url).text))

    def ping(self, service):
        return self.call(service, 'ping')
