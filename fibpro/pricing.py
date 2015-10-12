from math import log as logarithm, floor
from util import log

def price_request(requested_fib):
    return int(floor(logarithm(requested_fib,10))) + 1

def update_user_credit(requested_fib, user_obj):
    request_cost = price_request(requested_fib)
    if user_obj.credit < request_cost:
        return "Error: fib(%s) costs %s, user %s has insufficient credit(%s)" % (
            requested_fib, request_cost, user_obj.username, user_obj.credit)
    user_obj.credit -= request_cost
    log.info("%s used %s credit, balance: %s" % (
        user_obj.username, request_cost, user_obj.credit))
    return True


