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
from urlparse import parse_qs
# fibpro modules
from const import DEFAULT_SENTRY_DSN, DEFAULT_ENVIRONMENT
from servicedir import get_default_endpoints
from http import http_response, get_request_id
from util import (urlsafe_base64_encode,
    urlsafe_base64_decode, get_threadlocal,
    dict_set, dict_get)

log = getLogger('gunicorn.error')

def get_request_meta():
    request_meta = dict_get(get_threadlocal(), ["request_meta"], {})
    # write back dictionary in case it was newly created
    set_request_meta(request_meta)
    return request_meta

def set_request_meta(request_meta):
    return dict_set(get_threadlocal(), ["request_meta"], request_meta)

def get_server_meta():
    server_meta = dict_get(get_threadlocal(), ["server_meta"], {})
    set_server_meta(server_meta)
    return server_meta

def set_server_meta(server_meta):
    return dict_set(get_threadlocal(), ["server_meta"], server_meta)

class RemoteException(Exception):
    pass

class ServerConfig(object):

    def __init__(self):
        self.endpoints = get_default_endpoints()

    def _get_environment(self):
        return get_server_meta().get('environment', DEFAULT_ENVIRONMENT)

    def get_endpoint(self, service, environment=None):
        environment = environment or self._get_environment()
        is_custom_endpoint = False
        endpoint = self.endpoints[environment].get(service)
        custom_endpoint = get_request_meta().get('custom_endpoints', {}).get(service, None)
        if custom_endpoint:
            is_custom_endpoint = True
            endpoint = custom_endpoint
        return endpoint, is_custom_endpoint

    def get_services(self):
        return self.endpoints.keys()

class RPCBase(object):

    REQ_PARAM = 'req'
    LOG_RPC = False

    def log_rpc(self, from_service, to_service, method, args):
        if self.LOG_RPC:
            log.info("RPC %s %s->%s:%s(**%s)" % (
                get_request_id() or "-",
                from_service or "unknown",
                to_service or "unknown",
                method,
                str(args)))

    def set_server_name(self, name=None):
        return dict_set(get_server_meta(), ["name"], name or self.NAME)

    def set_environment(self, environment=None):
        return dict_set(get_server_meta(),
            ["environment"], environment or DEFAULT_ENVIRONMENT)

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

    def get_request_meta_dict(self):
        meta_dict = get_request_meta()
        meta_dict['source'] = get_server_meta().get('name', 'unknown')
        return meta_dict

    def encode_arguments(self, method, args):
        return urlsafe_base64_encode(
            self.encode_data(
                {
                    'request_meta': self.get_request_meta_dict(),
                    'method': method,
                    'args': args
                }))

    def decode_arguments(self, encoded_data):
        data = json.loads(urlsafe_base64_decode(encoded_data))
        return data['method'], data['args'], data.get('request_meta', {})

class Server(RPCBase):

    NAME = "unknown"
    SENTRY_DSN =  DEFAULT_SENTRY_DSN

    def __init__(self, environment=DEFAULT_ENVIRONMENT, name=None):
        self.set_environment(environment)
        self.set_server_name(name)
        self.service_init()

    def service_init(self):
        pass

    def wsgi_app(self, environ, start_response):
        query_dict = parse_qs(environ['QUERY_STRING'])
        method, args, request_meta = self.decode_arguments(
            query_dict[self.REQ_PARAM][0])
        set_request_meta(request_meta)
        self.log_rpc(
            get_request_meta().get('source', 'unknown'),
            self.NAME, method, args)
        try:
            result = getattr(self, method)(**args)
            body = self.encode_result(result)
        except Exception, e:
            body = self.encode_exception(traceback.format_exc())
        response = http_response(start_response, body=body)
        # clear request meta
        set_request_meta({})
        return response

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
        endpoint, is_custom = self.server_config.get_endpoint(service)
        if is_custom and self.LOG_RPC:
            log.info("Using custom %s endpoint %s" % (service, endpoint))
        return "%s?%s=%s" % (
            endpoint,
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
            get_server_meta().get("name"),
            service, method, args)
        return self.return_or_raise(
            self.decode_result(requests.get(url).text))

    def ping(self):
        return self.call('ping')

class DynamicObject:
    def __init__(self, **fields):
        self.__dict__.update(fields)
