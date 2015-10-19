from const import HOSTNAME

def get_default_endpoints():
    return {
        'logsink': "http://{}/api/logsink/".format(HOSTNAME),
        'userstore': "http://{}/api/userstore/".format(HOSTNAME),
        'pricing': "http://{}/api/pricing/".format(HOSTNAME),
        'compute_worker': "http://{}/api/compute_worker/".format(HOSTNAME),
        }
