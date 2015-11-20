from fibpro.reqtool.exchange import HTTPRequest, HTTPResponse
from fibpro.reqtool.proxy import WSGIProxy

class RecordingProxy(WSGIProxy):

    def __init__(self, wsgi_app, session=None):
        super(RecordingProxy, self).__init__(wsgi_app, self.on_request, self.on_response)
        self.session = session if session is not None else []
        self.current_exchange = None

    def _open_exchange(self):
        self.current_exchange = [HTTPRequest(), None]

    def _close_exchange(self):
        self.session.append(self.current_exchange)

    def on_request(self, environ):
        self._open_exchange()
        self.current_exchange[0].read(environ)

    def on_response(self, status=None, headers=None, body=None):
        self.current_exchange[1] = HTTPResponse(
            status=status,
            headers=headers,
            body=body)
        self._close_exchange()
