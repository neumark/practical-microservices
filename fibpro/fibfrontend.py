#!/usr/bin/env python
from raven import Client as RavenClient
from raven.middleware import Sentry
from const import DEFAULT_SENTRY_DSN
from rpc import Server
from http import HTTPBasic, http_response, set_request_id
from userstore import UserStoreClient
from pricing import PricingClient
from logsink import LogSinkClient

class FibFrontendServer(Server):

    NAME = "fibfrontend"
    
    def __init__(self):
        self.set_server_name()
        self.log = LogSinkClient()
        self.userstore_client = UserStoreClient()
        self.pricing_client = PricingClient()

    def calculate_fib(self, n):
        a, b = 0, 1
        for i in range(n):
            a, b = b, a + b
        return a

    def wsgi_app(self, environ, start_response):
        set_request_id()
        # get user object
        user_obj = environ.get('REMOTE_USER')
        # parse integer fibonacci sequence index
        try:
            requested_fib = int(environ['PATH_INFO'][1:])
        except ValueError, e:
            self.log.warn('Request to %s resulted in %s' % (
                environ['PATH_INFO'], str(e)))
            return http_response(start_response,
                status="404 NOT FOUND",
                body=str(e))
        # verify and update user credit
        credit_ok, pricing_response = self.pricing_client.pay_for_user_request(
            requested_fib, user_obj.username)
        if credit_ok != True:
            return http_response(start_response,
                    status="403 FORBIDDEN",
                    body=pricing_response)
        # return requested fibonacci number
        return http_response(start_response,
            body=self.calculate_fib(requested_fib))

    def app(self):
        return Sentry(
            HTTPBasic(
                self.wsgi_app,
                self.userstore_client),
            RavenClient(DEFAULT_SENTRY_DSN))
