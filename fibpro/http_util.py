import random
from fibpro.util import get_threadlocal, dict_set, dict_get

def generate_request_id():
    return ("r%16x" % random.getrandbits(63)).replace(' ', '0')

def set_new_request_id():
    request_id = generate_request_id()
    dict_set(get_threadlocal(), ["request_meta", "request_id"], request_id)
    return request_id 

def get_request_id():
    return dict_get(get_threadlocal(), ["request_meta", "request_id"], None)

def http_response(start_response, status="200 OK", body="", extra_headers=None):
    body_str = str(body)
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", 
            str(len(body_str)))
    ]
    if extra_headers:
        headers.extend(extra_headers)
    # add request id for gunicorn access log
    request_id = get_request_id()
    if request_id:
        headers.append(("x-request-id", request_id))
    start_response(status, headers)
    return iter([body_str])

class HTTPBasic(object):
    # based on: http://wsgi.readthedocs.org/en/latest/specifications/simple_authentication.html
    def __init__(self, app, userstore_client, realm='Website'):
        self.app = app
        self.userstore_client = userstore_client
        self.realm = realm

    def __call__(self, environ, start_response):
        def repl_start_response(status, headers, exc_info=None):
            if status.startswith('401') or not environ.get('REMOTE_USER', False):
                return self.bad_auth(environ, start_response)
            return start_response(status, headers)
        auth = environ.get('HTTP_AUTHORIZATION')
        if auth:
            scheme, data = auth.split(None, 1)
            assert scheme.lower() == 'basic'
            username, password = data.decode('base64').split(':', 1)
            user_obj = self.userstore_client.get_user(username)
            if  user_obj is None or user_obj.password != password:
                return self.bad_auth(environ, start_response)
            environ['REMOTE_USER'] = user_obj.username
            del environ['HTTP_AUTHORIZATION']
            return self.app(environ, repl_start_response)
        return self.bad_auth(environ, start_response)

    def bad_auth(self, environ, start_response):
        body = 'Please authenticate'
        headers = [
            ('content-type', 'text/plain'),
            ('content-length', str(len(body))),
            ('WWW-Authenticate', 'Basic realm="%s"' % self.realm)]
        start_response('401 Unauthorized', headers)
        return [body]
