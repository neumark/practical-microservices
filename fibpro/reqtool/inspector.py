from wsgi_proxy import WSGIProxyApplication 
from fibpro.http_util import http_response
from fibpro.rpc import set_server_meta
from fibpro.reqtool.record import RecordingProxy
from fibpro.servicedir import ServiceDirClient
from fibpro.util import urlsafe_base64_decode
import json
import urlparse
from logging import getLogger

log = getLogger('gunicorn.error')

HOST = '127.0.0.1'
PORT = 9999
ENVIRONMENT = 'prod'

class Inspector(object):

    def __init__(self):
        self.session = []
        self.recording_proxy = RecordingProxy(WSGIProxyApplication(), self.session)
        self.service_dir_client = ServiceDirClient()
        self.routes = {}
        self.endpoint_parts = dict(
            host=HOST,
            port=PORT)

    def add_route(self, service, parsed_endpoint):
        path = parsed_endpoint.path
        log.info('adding route %s to %s' % (path, service))
        self.routes[path] = (service, parsed_endpoint)

    def update_service_endpoint(self, service, parsed_endpoint):
        self.routes[parsed_endpoint.path] = (service, parsed_endpoint)
        endpoint_parts = dict(self.endpoint_parts)
        # remove starting '/'
        endpoint_parts['path'] = parsed_endpoint.path[1:]
        self.service_dir_client.set_endpoint(
            environment=ENVIRONMENT,
            service=service,
            endpoint_parts=endpoint_parts)

    def install_service_inspector(self, service, endpoint):
        parsed_endpoint = urlparse.urlparse(endpoint)
        self.add_route(service, parsed_endpoint)
        self.update_service_endpoint(service, parsed_endpoint)

    def install(self):
        self.original_endpoints = self.service_dir_client.get_all_endpoints(environment=ENVIRONMENT)
        log.info(self.original_endpoints)
        for service, endpoint in self.original_endpoints.iteritems():
            if service not in ['logsink', 'compute_worker']:
                continue
            self.install_service_inspector(service, endpoint)

    def app(self):
        set_server_meta({'name': 'inspector'})
        self.install()
        return self.wsgi_app

    def get_session_json(self):
        data = []
        for exchange in self.session:
            req = dict(exchange[0].__dict__)
            req['url'] = urlparse.urlunparse(exchange[0].url)
            req['call'] = json.loads(urlsafe_base64_decode(str(exchange[0].query['req'][0])))
            data.append({
                'request': req,
                'response': exchange[1].__dict__})
        return json.dumps(data)

    def dump_session(self, environ, start_response):
        return http_response(
            start_response,
            body=self.get_session_json())

    def restore_endpoints(self, environ, start_response):
        self.service_dir_client.set_all_endpoints(
                environment=ENVIRONMENT,
                endpoints=self.original_endpoints)
        return http_response(
            start_response,
            body=json.dumps(self.original_endpoints))

    def route_request(self, environ, start_response):
        """ overwrite host and port in environ
        before invoking wsgi proxy """
        requested_path = environ['PATH_INFO']
        if requested_path in self.routes:
            real_url = self.routes[requested_path][1]
            environ['HTTP_HOST'] = real_url.netloc
            response = self.recording_proxy(environ, start_response)
            log.info('proxied %s' % self.routes[requested_path][0])
            return response
        else:
            log.error('No souch route: %s' % requested_path)
            return http_response(start_response, "404 NOT FOUND")

    def wsgi_app(self, environ, start_response):
        if environ['PATH_INFO'] == '/session/':
            return self.dump_session(environ, start_response)
        if environ['PATH_INFO'] == '/restore/':
            return self.restore_endpoints(environ, start_response)
        return self.route_request(environ, start_response)
