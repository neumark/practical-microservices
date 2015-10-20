#!/usr/bin/env python
from raven import Client as RavenClient
from raven.middleware import Sentry
from const import (DEFAULT_SENTRY_DSN,
    DEFAULT_ENVIRONMENT,
    ENDPOINT_OVERRIDE_PREFIX)
from rpc import Server, get_request_meta, set_request_meta
from http import HTTPBasic, http_response, set_new_request_id
from userstore import UserStoreClient
from pricing import PricingClient
from logsink import LogSinkClient
from compute_worker import ComputeWorkerClient
from urlparse import parse_qs
from urllib import unquote

class FibFrontendServer(Server):

    NAME = "fibfrontend"
    
    def server_init(self):
        self.log = LogSinkClient()
        self.userstore_client = UserStoreClient()
        self.pricing_client = PricingClient()
        self.compute_worker_client = ComputeWorkerClient()

    def get_requested_fib(self, environ):
        # parse integer fibonacci sequence index
        try:
            return int(environ['PATH_INFO'][1:]), None, None
        except ValueError, e:
            self.log.warn('Request to %s resulted in %s' % (
                environ['PATH_INFO'], str(e)))
            return None, "404 NOT FOUND", str(e)

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
        user_obj = environ.get('REMOTE_USER')
        query_dict = parse_qs(environ['QUERY_STRING'])
        self.set_custom_environment(query_dict)
        self.set_custom_endpoints(query_dict)
        requested_fib, status, body = self.get_requested_fib(environ)
        return user_obj.username, requested_fib, status, body 

    def wsgi_app(self, environ, start_response):
        set_new_request_id()
        # get user object
        username, requested_fib, status, body = self.parse_request(environ)
        if requested_fib is not None:
            # verify and update user credit
            credit_ok, pricing_response = self.pricing_client.pay_for_user_request(
                requested_fib, username)
            status = "403 FORBIDDEN"
            body = pricing_response
            if credit_ok:
                status = "200 OK"
                body = self.compute_worker_client.compute_fib(requested_fib)
            # return requested fibonacci number
        response = http_response(start_response,
            status=status,
            body=body)
        # clear request meta
        set_request_meta({})
        return response

    def app(self):
        return Sentry(
            HTTPBasic(
                self.wsgi_app,
                self.userstore_client),
            RavenClient(DEFAULT_SENTRY_DSN))
