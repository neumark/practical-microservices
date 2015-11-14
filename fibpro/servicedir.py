from config import (PROD_HOSTNAME, PROD_PORT, DEV_HOSTNAME, SERVICE_UPDATE_INTERVAL,
    DEFAULT_SERVICE_DIR_ENDPOINT, DEFAULT_ENVIRONMENT)
from rpc import Client, Server, get_request_meta, get_server_meta, set_server_meta
from util import load_config, dict_map_string, dict_set, dict_get
from logging import getLogger
from gevent import spawn, sleep

class ServiceDirBase(object):
    NAME = "servicedir"
    LOG_RPC = True
    # servicedir must log to stderr instead of logsink
    log = getLogger('gunicorn.error')

class ServiceDirServer(ServiceDirBase, Server):

    def server_init(self):
        self.service_endpoints = {}

    def register_server(self):
        pass

    def get_environments(self):
        return self.service_endpoints.keys()

    def get_services(self, environment=DEFAULT_ENVIRONMENT):
        return dict_get(self.service_endpoints, ['environment'], {}).keys()

    def get_endpoint(self, environment=DEFAULT_ENVIRONMENT, service=None):
        return dict_get(self.service_endpoints, [environment, service], None)

    def get_all_endpoints(self, environment=None):
        if environment is None:
            return self.service_endpoints
        return dict_get(self.service_endpoints, [environment], {})

    def set_endpoint(self, environment=DEFAULT_ENVIRONMENT, service=None, endpoint_parts=None):
        endpoint = "{scheme}://{host}:{port}/{path}".format(
            scheme=endpoint_parts.get('scheme', 'http'),
            host=get_request_meta().get('environ')['REMOTE_ADDR'],
            port=endpoint_parts['port'],
            path=endpoint_parts['path'])
        self.log.info("Registering endpoint %s:%s = %s" % (
            environment, service, endpoint))
        dict_set(self.service_endpoints, [environment, service], endpoint)
        return endpoint

class ServiceDirClient(ServiceDirBase, Client):

    def __init__(
            self,
            service_dir_endpoint=None):
        self.service_dir_endpoint = service_dir_endpoint or DEFAULT_SERVICE_DIR_ENDPOINT
        self.service_dir_client = self
        self.service_endpoints = {}
        self._init_timer()

    def _init_timer(self):
        def poll_endpoints(server_meta):
            # set server meta for this thread
            set_server_meta(server_meta)
            while True:
                self.service_endpoints = self.get_all_endpoints(
                    dict_get(
                        get_server_meta(),
                        ["environment"],
                        DEFAULT_ENVIRONMENT))
                sleep(SERVICE_UPDATE_INTERVAL)
        spawn(poll_endpoints, get_server_meta())

    def get_endpoint(self, environment, service):
        if service == "servicedir":
            return self.service_dir_endpoint
        if self.service_endpoints and \
                service in self.service_endpoints.get(environment, {}):
            endpoint = self.service_endpoints[environment][service]
            if endpoint is not None:
                return endpoint
        # fall back to making RPC request
        self.log.info("No cached endpoint for %s; polling servicedir" % service)
        return self.call('get_endpoint', {
            'environment': environment,
            'service': service})

    def set_endpoint(self, environment, service, endpoint_parts):
        return self.call('set_endpoint', {
            'environment': environment,
            'service': service,
            'endpoint_parts': endpoint_parts})

    def get_services(self, environment):
        return self.call('get_services', {
            'environment': environment})

    def get_environments(self):
        return self.call('get_environments')

    def get_all_endpoints(self, environment=None):
        return self.call('get_all_endpoints', {
            'environment': environment})

    def _get_current_environment(self):
        # first, try to get environment from request_meta,
        # then from server_meta, then use default
        return get_request_meta().get(
            'environment',
            get_server_meta().get('environment',
                DEFAULT_ENVIRONMENT))

    def _get_endpoint_with_overrides(self, environment, service):
        is_custom_endpoint = False
        endpoint = self.get_endpoint(environment, service)
        custom_endpoint = get_request_meta().get('custom_endpoints', {}).get(service, None)
        if custom_endpoint:
            is_custom_endpoint = True
            # custom_endpoint could be an environment name
            # or an endpoint url
            # TEMPORARILY DISABLE
            # if custom_endpoint in self.get_environments():
            #    endpoint = self.endpoints[custom_endpoint].get(service)
            #else:
            endpoint = custom_endpoint
        return endpoint, is_custom_endpoint

    def get_effective_endpoint(self, service):
        """ returns effective endpoint for service with overrides. """
        environment = self._get_current_environment()
        return self._get_endpoint_with_overrides(environment, service)
