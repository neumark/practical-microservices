from config import (PROD_HOSTNAME, PROD_PORT, DEV_HOSTNAME, SERVICE_CONFIG_FILE, DEFAULT_SERVICE_DIR_ENDPOINT, DEFAULT_ENVIRONMENT)
from rpc import Client, Server, ServerConfig
from util import load_config, dict_map_string
from logsink import LogSinkClient

class ServiceDirBase(object):
    NAME = "servicedir"
    LOG_RPC = True

class ServiceDirServer(ServiceDirBase, Server):

    def server_init(self):
        self.log = LogSinkClient()
        self.service_endpoints = self._load_service_config()

    def _substitute_constants(self, contents):
        return contents.format(
            PROD_HOSTNAME=PROD_HOSTNAME,
            PROD_PORT=PROD_PORT,
            DEV_HOSTNAME=DEV_HOSTNAME)

    def _load_service_config(self):
        return dict_map_string(
            load_config(SERVICE_CONFIG_FILE),
            self._substitute_constants)
 
    def get_environments(self):
        return self.service_endpoints.keys()

    def get_services(self, environment=DEFAULT_ENVIRONMENT):
        return self.service_endpoints[environment].keys()

    def get_endpoint(self, environment=DEFAULT_ENVIRONMENT, service=None):
        return self.service_endpoints[environment][service]

class ServiceDirClient(ServiceDirBase, Client):

    def __init__(
            self,
            service_dir_endpoint=DEFAULT_SERVICE_DIR_ENDPOINT):
        self.service_dir_endpoint = service_dir_endpoint
        self.server_config = ServerConfig(service_dir_client=self)

    def get_endpoint(self, environment, service):
        if service == "servicedir":
            return self.service_dir_endpoint
        return self.call('get_endpoint', {
            'environment': environment,
            'service': service})

    def get_services(self, environment):
        return self.call('get_services', {
            'environment': environment})

    def get_environments(self):
        return self.call('get_environments')
