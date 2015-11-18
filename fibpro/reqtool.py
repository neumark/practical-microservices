from wsgi_intercept import requests_intercept, add_wsgi_intercept
from wsgi_proxy import WSGIProxyApplication, reconstruct_url
import sys
import urlparse
from httplib import HTTPConnection
from fibpro.logsink import LogSinkClient
from fibpro.userstore import UserStoreServer, UserStoreClient

class Transaction(object):
    def __init__(self):
        self.request = {}
        self.response = {}

    def __repr__(self):
        return "Transaction(%s, %s)" % (repr(self.request), repr(self.response))

class RecordingProxy(object):

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self.transactions = []

    def start_response_proxy(self, start_response, current_transaction):
        def proxy(status, headers):
            current_transaction.request['status'] = status
            current_transaction.request['headers'] = headers 
            start_response(status, headers)
        return proxy

    def __call__(self, environ, start_response):
        current_transaction = Transaction()
        current_transaction.request['url'] = urlparse.urlparse(reconstruct_url(environ))
        response_iter = self.wsgi_app(environ, self.start_response_proxy(start_response, current_transaction))
        response_body = "".join([chunk for chunk in response_iter])
        current_transaction.response['body'] = response_body
        self.transactions.append(current_transaction)
        return iter([response_body])

def intercept(host, port, app):
    add_wsgi_intercept(host, port, lambda: app)

requests_intercept.install()
#proxy = RecordingProxy(UserStoreServer(register=False).app())
proxy = RecordingProxy(WSGIProxyApplication())
intercept('127.0.0.1', 9003, proxy)
UserStoreClient().get_user("username")
print proxy.__dict__
