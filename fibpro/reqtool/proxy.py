class WSGIProxy(object):

    def __init__(self, wsgi_app, on_request=None, on_response=None):
        self.wsgi_app = wsgi_app
        self.on_request = on_request
        self.on_response = on_response

    def start_response_proxy(self, start_response, response_data):
        def proxy(status, headers):
            response_data['status'] = status
            response_data['headers'] = headers 
            start_response(status, headers)
        return proxy

    def __call__(self, environ, start_response):
        if self.on_request:
            self.on_request(environ)
        response_data = {}
        response_iter = self.wsgi_app(environ, self.start_response_proxy(start_response, response_data))
        response_data['body'] = "".join([chunk for chunk in response_iter])
        if self.on_response:
            self.on_response(**response_data)
        return iter([response_data['body']])


