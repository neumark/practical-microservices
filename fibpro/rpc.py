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
from urlparse import parse_qs
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

def get_request_meta():
    return getattr(get_threadlocal(), "request_meta", {})

class RemoteException(Exception):
    pass

class ServerConfig(object):

    def __init__(self):
        self.endpoints = get_default_endpoints()

    def get_endpoint(self, service):
        return self.endpoints[service]

class RPCBase(object):

    REQ_PARAM = 'req'
    LOG_RPC = False

    def log_rpc(self, from_service, to_service, method, args):
        if self.LOG_RPC:
            log.info("RPC %s->%s:%s(**%s)" % (
                from_service,
                to_service,
                method,
                str(args)))

    def set_server_name(self):
        setattr(get_threadlocal(), "server_name", self.NAME)

    def get_server_name(self):
        return getattr(get_threadlocal(), "server_name", "unknown")

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
                    'request_meta': {
                        'source': self.get_server_name()},
                    'method': method,
                    'args': args
                }))

    def decode_arguments(self, encoded_data):
        data = json.loads(urlsafe_base64_decode(encoded_data))
        return data['method'], data['args'], data.get('request_meta', {})

class Server(RPCBase):

    NAME = "unknown"
    SENTRY_DSN =  DEFAULT_SENTRY_DSN

    def wsgi_app(self, environ, start_response):
        query_dict = parse_qs(environ['QUERY_STRING'])
        method, args, request_meta = self.decode_arguments(
            query_dict[self.REQ_PARAM][0])
        self.log_rpc(
            request_meta.get('source', 'unknown'),
            self.NAME, method, args)
        setattr(get_threadlocal(), "request_meta", request_meta)
        try:
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
        return "%s?%s=%s" % (
            self.server_config.get_endpoint(service),
            self.REQ_PARAM,
            self.encode_arguments(method, args))

    def return_or_raise(self, response):
        if 'result' in response:
            return response['result']
        raise RemoteException(response['traceback'])

    def call(self, method, args=None, service=None):
        args = args or {}
        service = service or self.NAME
        url = self.construct_url(
            method, args, service)
        self.log_rpc(
            self.get_server_name(), service, method, args)
        return self.return_or_raise(
            self.decode_result(requests.get(url).text))

    def ping(self):
        return self.call('ping')

class DynamicObject:
    def __init__(self, **fields):
        self.__dict__.update(fields)
