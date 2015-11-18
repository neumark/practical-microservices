from fibpro.rpc import Client, Server
from fibpro.logsink import LogSinkClient
from fibpro.pricing import PricingClient
from fibpro.compute_worker import ComputeWorkerClient

class ControllerBase(object):
    NAME = "controller"
    LOG_RPC = True

class ControllerServer(ControllerBase, Server):

    def server_init(self):
        self.log = LogSinkClient(self.service_dir_client)
        self.pricing_client = PricingClient(self.service_dir_client)
        self.compute_worker_client = ComputeWorkerClient(self.service_dir_client)

    def parse_requested_fib(self, raw_requested_fib):
        try:
            return int(raw_requested_fib)
        except ValueError, e:
            self.log.warn('Request to %s resulted in %s' % (
                raw_requested_fib, str(e)))
            return None

    def call_compute_worker(self, requested_fib):
        return self.compute_worker_client.compute_fib(requested_fib)

    def generate_response(self, raw_requested_fib=None, username=None):
        requested_fib = self.parse_requested_fib(raw_requested_fib)
        if requested_fib is None:
            return ["404 NOT FOUND", "404: %s" % raw_requested_fib]
        # verify and update user credit
        credit_ok, pricing_response = self.pricing_client.pay_for_user_request(
            requested_fib, username)
        if credit_ok:
            return ["200 OK", self.call_compute_worker(requested_fib)]
        return ["403 FORBIDDEN", pricing_response]

class ControllerClient(ControllerBase, Client):

    # runs in the client process
    def generate_response(self, raw_requested_fib, username):
        return self.call('generate_response', {
            'raw_requested_fib': raw_requested_fib,
            'username': username})
