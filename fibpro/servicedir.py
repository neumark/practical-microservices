from const import HOSTNAME

client_constructors = {}

def get_default_endpoints():
    return {
        'logsink': "http://{}/api/logsink/".format(HOSTNAME),
        'userstore': "http://{}/api/userstore/".format(HOSTNAME),
        'pricing': "http://{}/api/pricing/".format(HOSTNAME)
        # services to be factored out of fibfrontend in the future:
        #'compute': "http://{}/api/compute/".format(HOSTNAME),
        }
