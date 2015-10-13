from math import log as logarithm, floor
from logsink import log
from userstore import UserStoreClient

userstore_client = UserStoreClient()

def price_request(requested_fib):
    return int(floor(logarithm(requested_fib,10))) + 1

def update_user_credit(requested_fib, user_obj):
    request_cost = price_request(requested_fib)
    credit = userstore_client.get_credit(user_obj.username)
    if credit < request_cost:
        log.info(
            'User "%s" denied fib(%s), credit: %s' % (
            user_obj.username,
            requested_fib,
            credit))
        return "Error: fib(%s) costs %s, user %s has insufficient credit(%s)" % (
            requested_fib, request_cost, user_obj.username, credit)
    userstore_client.increment_credit(
        user_obj.username, -1 * request_cost)
    log.info("%s used %s credit, balance: %s" % (
        user_obj.username, request_cost, credit))
    return True

