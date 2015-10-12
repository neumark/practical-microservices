# based on: http://wsgi.readthedocs.org/en/latest/specifications/simple_authentication.html
from logsink import log

class HTTPBasic(object):

    def __init__(self, app, get_user, realm='Website'):
        self.app = app
        self.get_user = get_user
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
            user_obj = self.get_user(username)
            if  user_obj is None or user_obj.password != password:
                return self.bad_auth(environ, start_response)
            environ['REMOTE_USER'] = user_obj
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

def remove_header(headers, name):
    for header in headers:
        if header[0].lower() == name.lower():
            headers.remove(header)
            break
