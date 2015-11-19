#!/usr/bin/env python
from urlparse import parse_qs
from urllib import unquote
from raven import Client as RavenClient
from raven.middleware import Sentry
from .config import (DEFAULT_SENTRY_DSN,
    DEFAULT_ENVIRONMENT,
    ENDPOINT_OVERRIDE_PREFIX)
from fibpro.rpc import Server, GenericClient, get_request_meta, set_request_meta
from fibpro.http_util import HTTPBasic, http_response, set_new_request_id
from fibpro.userstore import UserStoreClient
from fibpro.logsink import LogSinkClient
from fibpro.util import get_threadlocal, dict_set, dict_get

class GatekeeperServer(Server):

    NAME = "gatekeeper"
    
    def server_init(self):
        self.log = LogSinkClient(self.service_dir_client)
        self.userstore_client = UserStoreClient(self.service_dir_client)
        self.controller_client = GenericClient(self.service_dir_client, name="controller")
        self.basic_auth = HTTPBasic(self.wsgi_app_post_auth, self.userstore_client) 

    def get_requested_fib(self, environ):
        # parse integer fibonacci sequence index
        return environ['PATH_INFO'][1:]

    def set_custom_environment(self, query_dict):
        if "environment" in query_dict:
            # environments set in the request should be
            # stored in request_meta, not server_meta.
            # Storing environment in request_meta will
            # propagate it to other services as well.
            environment = query_dict['environment'][-1]
            get_request_meta()['environment'] = environment
            self.log.info('Using custom environment: %s' % environment)
            return environment
 
    def set_custom_endpoints(self, query_dict):
        # custom enpoint information travels on in request_meta
        custom_endpoints = {}
        for key in query_dict.keys():
            if key.startswith(ENDPOINT_OVERRIDE_PREFIX):
                endpoint = key[(len(ENDPOINT_OVERRIDE_PREFIX)):]
                custom_endpoints[endpoint] = query_dict[key][-1]
        if custom_endpoints:
            get_request_meta()['custom_endpoints'] = custom_endpoints
            self.log.info('Using custom endpoints: %s' % str(custom_endpoints))
        return custom_endpoints

    def parse_request(self, environ):
        query_dict = parse_qs(environ['QUERY_STRING'])
        self.set_custom_environment(query_dict)
        self.set_custom_endpoints(query_dict)
        return self.get_requested_fib(environ)

    def wsgi_app_post_auth(self, environ, start_response):
        username = environ.get('REMOTE_USER', None)
        if username is not None:
            raw_requested_fib = self.parse_request(environ)
            status, body = self.controller_client.generate_response(
                raw_requested_fib=raw_requested_fib,
                username=username)
        else:
            status, body = ["401 UNAUTHENTICATED", "Please log in"]
        return http_response(start_response, status, body)

    def wsgi_app(self, environ, start_response):
        self.set_environment(self.environment)
        self.set_server_name(self.name)
        set_new_request_id()
        response = self.basic_auth(environ, start_response)
        # clear request meta
        set_request_meta({})
        return response
