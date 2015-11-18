from math import log as logarithm, floor
from fibpro.rpc import Client, Server, get_threadlocal, get_request_meta
from fibpro.userstore import UserStoreClient
from fibpro.logsink import LogSinkClient

class PricingBase(object):
    NAME = "pricing"
    LOG_RPC = True

class PricingServer(PricingBase, Server):

    def server_init(self):
        self.log = LogSinkClient(self.service_dir_client)
        self.userstore_client = UserStoreClient(self.service_dir_client)

    def price_request(self, requested_fib):
        return int(floor(logarithm(requested_fib,10))) + 1

    def pay_for_user_request(self, requested_fib, username):
        request_cost = self.price_request(requested_fib)
        credit = self.userstore_client.get_credit(username)
        if credit < request_cost:
            self.log.info(
                'User "%s" denied fib(%s), credit: %s' % (
                username,
                requested_fib,
                credit))
            return [
                False,
                "Error: fib(%s) costs %s, user %s has insufficient credit(%s)" % (
                requested_fib, request_cost, username, credit)]
        new_credit = self.userstore_client.increment_credit(
            username, -1 * request_cost)
        self.log.info("%s used %s credit, balance: %s" % (
            username, request_cost, new_credit))
        return [True, new_credit]

class PricingClient(PricingBase, Client):

    def pay_for_user_request(self, requested_fib, username):
        return self.call('pay_for_user_request', {
            'requested_fib': requested_fib,
            'username': username})


