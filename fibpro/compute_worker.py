from rpc import Client, Server, ServerConfig
from userstore import UserStoreClient
from logsink import LogSinkClient

class ComputeWorkerBase(object):
    NAME = "compute_worker"
    LOG_RPC = True
    log = LogSinkClient()

class ComputeWorkerServer(ComputeWorkerBase, Server):

    userstore_client = UserStoreClient()

    def __init__(self):
        self.set_server_name()
 
    def compute_fib(self, requested_fib):
        a, b = 0, 1
        for i in range(requested_fib):
            a, b = b, a + b
        return a

class ComputeWorkerClient(ComputeWorkerBase, Client):

    def compute_fib(self, requested_fib):
        return self.call('compute_fib', {
            'requested_fib': requested_fib})


