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
from config import (DEFAULT_SENTRY_DSN, DEFAULT_ENVIRONMENT,
    WAIT_FOR_SERVICE_ENDPOINT_TIMEOUT)
from http import http_response, get_request_id
from util import (urlsafe_base64_encode,
    urlsafe_base64_decode, get_threadlocal,
    dict_set, dict_get, get_server_port, retry)
from gevent import getcurrent
from time import sleep

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

class NoServiceEndpointFound(Exception):
    pass

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

    def get_server_name(self):
        return dict_get(get_server_meta(), ["name"])

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
        meta_dict = {k: v for k, v in get_request_meta().iteritems() if k != 'environ'}
        meta_dict['source'] = get_server_meta().get('name', 'unknown')
        meta_dict['source_environment'] = get_server_meta().get('environment')
        return meta_dict

    def encode_arguments(self, method, args):
        return urlsafe_base64_encode(
                self.encode_data(
                    {
                        'request_meta': self.get_request_meta_dict(),
                        'method': method,
                        'args': args
                        }))

    def decode_arguments(self, environ):
        query_dict = parse_qs(environ['QUERY_STRING'])
        encoded_data = query_dict[self.REQ_PARAM][0]
        data = json.loads(urlsafe_base64_decode(encoded_data))
        request_meta = data.get('request_meta', {})
        request_meta['environ'] = environ
        return data['method'], data['args'], request_meta

class Server(RPCBase):

    NAME = "unknown"
    SENTRY_DSN =  DEFAULT_SENTRY_DSN

    def __init__(self, environment=DEFAULT_ENVIRONMENT, name=None):
        self.environment = environment
        self.name = self.NAME or name
        self.set_environment(self.environment)
        self.set_server_name(self.name)
        self.server_init()
        self.register_server()

    def server_init(self):
        pass

    def register_server(self):
        environment = dict_get(get_server_meta(), ["environment"])
        service_name = dict_get(get_server_meta(), ["name"])
        endpoint_parts = {
            'port': get_server_port(),
            'path': "api/%s" % self.NAME,
        }
        from fibpro.servicedir import ServiceDirClient
        ServiceDirClient().set_endpoint(
            environment,
            service_name,
            endpoint_parts)

    def wsgi_app(self, environ, start_response):
        self.set_environment(self.environment)
        self.set_server_name(self.name)

        method, args, request_meta = self.decode_arguments(environ)
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

    def __init__(self, service_dir_endpoint=None):
        from servicedir import ServiceDirClient
        self.service_dir_client = ServiceDirClient(service_dir_endpoint)

    def _get_endpoint(self, service):
        endpoint, is_custom = self.service_dir_client.get_effective_endpoint(service)
        if endpoint is None:
            raise NoServiceEndpointFound('No endpoint found for %s' % service)
        if is_custom and self.LOG_RPC:
            log.info("Using custom %s endpoint %s" % (service, endpoint))
        return endpoint

    def construct_url(self, method, args, service):
        return "%s?%s=%s" % (
            self._get_endpoint(service),
            self.REQ_PARAM,
            self.encode_arguments(method, args))

    def return_or_raise(self, response):
        if 'result' in response:
            return response['result']
        raise RemoteException(response['traceback'])

    
    def call(self, method, args=None, service=None):
        args = args or {}
        service = service or self.NAME
        def no_service_endpoint(e):
            log.info("No endpoint found for %s, retrying" % service)
            sleep(WAIT_FOR_SERVICE_ENDPOINT_TIMEOUT)
        url = retry(
            lambda: self.construct_url(method, args, service),
            post_attempt=no_service_endpoint,
            raise_last_exception=True)
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
