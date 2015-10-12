#!/usr/bin/env python
# dependencies
from raven import Client
from raven.middleware import Sentry
# fibpro modules
from const import SENTRY_DSN
from util import (log, http_response,
    get_default_endpoints, urlsafe_base64_encode,
    urlsafe_base64_decode)
import base64
import json
import requests

class ServerConfig(object):
    def __init__(self):
        self.endpoints = get_default_endpoints()

class RPCBase(object):

    ARG_PREFIX = '?req='

    def encode_result(self, result):
        return json.dumps(
            result,
            separators=(',', ':'),
            sort_keys=True)

    def decode_result(self, response):
        return json.loads(response)

    def encode_arguments(self, method, args):
        return urlsafe_base64_encode(
            self.encode_result(
                {
                    'method': method,
                    'args': args
                }))

    def decode_arguments(self, encoded_data):
        print encoded_data
        data = json.loads(urlsafe_base64_decode(encoded_data))
        return data['method'], data['args']

class Server(RPCBase):
        
    def ping(self):
        return "pong"

    def wsgi_app(self, environ, start_response):
        try:
            method, args = self.decode_arguments(
                environ['QUERY_STRING'][(len(self.ARG_PREFIX)-1):])
            log.info('RPC request: %s(**%s)' % (
                method, self.encode_result(args)))
        except ValueError, e:
            log.warn('Request to %s resulted in %s' % (
                environ['PATH_INFO'], str(e)))
            return http_response(start_response,
                status="404 NOT FOUND",
                body=str(e))
        # TODO: no such method?
        # TODO: try-except
        returned = getattr(self, method)(**args)
        return http_response(start_response,
            body=self.encode_result(returned))

    def app(self):
        return self.wsgi_app

class Client(RPCBase):

    def __init__(self, server_config):
        self.server_config = server_config

    def construct_url(self, service, method, args):
        return "%s%s%s" % (
            self.server_config.endpoints[service],
            self.ARG_PREFIX,
            self.encode_arguments(method, args))

    def call(self, service, method, args):
        url = self.construct_url(service, method, args)
        return self.decode_result(requests.get(url).text)

    def ping(self, service):
        return self.call(service, 'ping', {})
