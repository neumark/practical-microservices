from wsgi_intercept import requests_intercept, add_wsgi_intercept
from wsgi_proxy import WSGIProxyApplication, reconstruct_url
import sys
import urlparse
from httplib import HTTPConnection
from fibpro.logsink import LogSinkClient
from fibpro.userstore import UserStoreServer, UserStoreClient
from fibpro.rpc import RPCBase
from StringIO import StringIO

class Transaction(object):
    def __init__(self):
        self.request = {}
        self.response = {}

    def _read_request_body(self, environ):
        try:
            body_length = int(environ['CONTENT_LENGTH'])
            request_body = environ['wsgi.input'].read(body_length)
            self.request['body_length'] = body_length
            self.request['body'] = request_body
            environ['wsgi.input'] = StringIO(request_body)
        except (KeyError, ValueError):
            pass

    def _read_request_url(self, environ):
        self.request['url'] = urlparse.urlparse(reconstruct_url(environ))

    def _read_request_call(self, environ):
        rpcbase = RPCBase()
        self.request['call'] = rpcbase.decode_arguments(environ)

    def _read_request_headers(self, environ):
        # from wsgi-proxy source
        headers = dict(
            (key, value)
            for key, value in (
                # This is a hacky way of getting the header names right
                (key[5:].lower().replace('_', '-'), value)
                for key, value in environ.items()
                # Keys that start with HTTP_ are all headers
                if key.startswith('HTTP_')
            )
        )
        # Handler headers that aren't HTTP_ in environ
        try:
            headers['content-type'] = environ['CONTENT_TYPE']
        except KeyError:
            pass
        # Add our host if one isn't defined
        if 'host' not in headers:
            headers['host'] = environ['SERVER_NAME']
        self.request['headers'] = headers


    def read_request(self, environ):
        self._read_request_url(environ)
        self._read_request_body(environ)
        self._read_request_headers(environ)
        self._read_request_call(environ)

    def __repr__(self):
        return "Transaction(%s, %s)" % (repr(self.request), repr(self.response))

class RecordingProxy(object):

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self.transactions = []

    def start_response_proxy(self, start_response, current_transaction):
        def proxy(status, headers):
            current_transaction.response['status'] = status
            current_transaction.response['headers'] = headers 
            start_response(status, headers)
        return proxy

    def __call__(self, environ, start_response):
        current_transaction = Transaction()
        current_transaction.read_request(environ)
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
