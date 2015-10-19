#!/usr/bin/env python
from raven import Client as RavenClient
from raven.middleware import Sentry
from const import DEFAULT_SENTRY_DSN
from rpc import Server
from http import HTTPBasic, http_response, set_request_id
from userstore import UserStoreClient
from pricing import PricingClient
from logsink import LogSinkClient
from compute_worker import ComputeWorkerClient

class FibFrontendServer(Server):

    NAME = "fibfrontend"
    
    def __init__(self):
        self.set_server_name()
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

    def wsgi_app(self, environ, start_response):
        set_request_id()
        # get user object
        user_obj = environ.get('REMOTE_USER')
        requested_fib, status, body = self.get_requested_fib(environ)
        if requested_fib is not None:
            # verify and update user credit
            credit_ok, pricing_response = self.pricing_client.pay_for_user_request(
                requested_fib, user_obj.username)
            status = "403 FORBIDDEN"
            body = pricing_response
            if credit_ok:
                status = "200 OK"
                body = self.compute_worker_client.compute_fib(requested_fib)
            # return requested fibonacci number
        return http_response(start_response,
            status=status,
            body=body)

    def app(self):
        return Sentry(
            HTTPBasic(
                self.wsgi_app,
                self.userstore_client),
            RavenClient(DEFAULT_SENTRY_DSN))
