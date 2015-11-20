import urlparse
from wsgi_proxy import reconstruct_url
from fibpro.rpc import RPCBase
from StringIO import StringIO

class HTTPMessage(object):
    def __init__(self, headers=None, body=None):
        self.body = body
        self.headers = headers

class HTTPRequest(HTTPMessage):
    def __init__(self, method=None, url=None, headers=None, body=None):
        super(HTTPRequest, self).__init__(headers, body)
        self.method = method
        self.url = url
        self.query = None

    def _read_request_body(self, environ):
        try:
            body_length = int(environ['CONTENT_LENGTH'])
            self.body = environ['wsgi.input'].read(body_length)
            environ['wsgi.input'] = StringIO(self.body)
        except (KeyError, ValueError):
            pass

    def _read_request_url(self, environ):
        self.url = urlparse.urlparse(reconstruct_url(environ))
        self.query = urlparse.parse_qs(self.url.query)

    def _read_request_method(self, environ):
        self.method = environ['REQUEST_METHOD'] 

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
        self.headers = headers

    def read(self, environ):
        self._read_request_method(environ)
        self._read_request_url(environ)
        self._read_request_headers(environ)
        self._read_request_body(environ)


class HTTPResponse(HTTPMessage):
    def __init__(self, status=None, headers=None, body=None):
        super(HTTPResponse, self).__init__(headers, body)
        self.status = status
