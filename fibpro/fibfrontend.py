#!/usr/bin/env python
from raven import Client as RavenClient
from raven.middleware import Sentry
from const import DEFAULT_SENTRY_DSN
from rpc import Server
from http_basic import HTTPBasic
from userstore import UserStoreClient
from util import http_response
from pricing import update_user_credit
from logsink import log

class FibFrontendServer(Server):

    NAME = "fibfrontend"
    
    def __init__(self):
        self.set_server_name()
        self.userstore_client = UserStoreClient()

    def calculate_fib(self, n):
        a, b = 0, 1
        for i in range(n):
            a, b = b, a + b
        return a

    def wsgi_app(self, environ, start_response):
        # get user object
        user_obj = environ.get('REMOTE_USER')
        # parse integer fibonacci sequence index
        try:
            requested_fib = int(environ['PATH_INFO'][1:])
        except ValueError, e:
            log.warn('Request to %s resulted in %s' % (
                environ['PATH_INFO'], str(e)))
            return http_response(start_response,
                status="404 NOT FOUND",
                body=str(e))
        # verify and update user credit
        credit_ok = update_user_credit(requested_fib, user_obj)
        if credit_ok != True:
            return http_response(start_response,
                    status="403 FORBIDDEN",
                    body=credit_ok)
        # return requested fibonacci number
        return http_response(start_response,
            body=self.calculate_fib(requested_fib))

    def app(self):
        return Sentry(
            HTTPBasic(
                self.wsgi_app,
                self.userstore_client),
            RavenClient(DEFAULT_SENTRY_DSN))
