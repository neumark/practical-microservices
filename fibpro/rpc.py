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
from threading import local
# fibpro modules
from const import DEFAULT_SENTRY_DSN
from servicedir import get_default_endpoints
from util import (http_response,
    urlsafe_base64_encode,
    urlsafe_base64_decode)

log = getLogger('gunicorn.error')
_threadlocal = None

def get_threadlocal():
    global _threadlocal
    if not _threadlocal:
        _threadlocal = local()
    return _threadlocal

class RemoteException(Exception):
    pass

class ServerConfig(object):
    def __init__(self):
        self.endpoints = get_default_endpoints()

class RPCBase(object):

    ARG_PREFIX = '?req='
    LOG_RPC = False

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

    def encode_arguments(self, method, args, source):
        return urlsafe_base64_encode(
            self.encode_data(
                {
                    'request_meta': {
                        'source': source},
                    'method': method,
                    'args': args
                }))

    def decode_arguments(self, encoded_data):
        data = json.loads(urlsafe_base64_decode(encoded_data))
        return data['method'], data['args'], data.get('request_meta', {})

class Server(RPCBase):

    NAME = "unknown"
    SENTRY_DSN =  DEFAULT_SENTRY_DSN

    def set_server_name(self):
        setattr(get_threadlocal(), "server_name", self.NAME)

    def wsgi_app(self, environ, start_response):
        method, args, request_meta = self.decode_arguments(
            environ['QUERY_STRING'][(len(self.ARG_PREFIX)-1):])
        if self.LOG_RPC:
            log.info('RPC server executing: %s:%s(**%s)' % (
                self.NAME, method, self.encode_result(args)))
        try:
            setattr(get_threadlocal(), "request_meta", request_meta)
            result = getattr(self, method)(**args)
            body = self.encode_result(result)
        except Exception, e:
            body = self.encode_exception(traceback.format_exc())
        return http_response(start_response,
            body=body)

    def app(self):
        return Sentry(self.wsgi_app,
            RavenClient(self.SENTRY_DSN))

    def ping(self):
        return "pong"

class Client(RPCBase):

    NAME = "unknown"

    def __init__(self, server_config=None):
        self.server_config = server_config or ServerConfig()

    def construct_url(self, method, args, service):
        source = getattr(get_threadlocal(), "server_name", "unknown")
        return "%s%s%s" % (
            self.server_config.endpoints[service],
            self.ARG_PREFIX,
            self.encode_arguments(method, args, source))

    def return_or_raise(self, response):
        if 'result' in response:
            return response['result']
        raise RemoteException(response['traceback'])

    def call(self, method, args=None, service=None):
        args = args or {}
        service = service or self.NAME
        url = self.construct_url(
            method, args, service)
        if self.LOG_RPC:
            log.info("RPC client calling %s:%s(**%s)" % (
                service, method, str(args)))
        return self.return_or_raise(
            self.decode_result(requests.get(url).text))

    def ping(self):
        return self.call('ping')

class DynamicObject:
    def __init__(self, **fields):
        self.__dict__.update(fields)
