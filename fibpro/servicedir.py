from const import HOSTNAME

def get_default_endpoints():
    return {
        'prod': {
            'logsink': "http://{}/api/logsink/".format(HOSTNAME),
            'userstore': "http://{}/api/userstore/".format(HOSTNAME),
            'pricing': "http://{}/api/pricing/".format(HOSTNAME),
            'compute_worker': "http://{}/api/compute_worker/".format(HOSTNAME),
            'controller': "http://{}/api/controller/".format(HOSTNAME)
            },
        'dev': {
            'logsink': "http://localhost:9102/api/logsink/",
            'userstore': "http://localhost:9103/api/userstore/",
            'pricing': "http://localhost:9104/api/pricing/",
            'compute_worker': "http://localhost:9105/api/compute_worker/",
            'controller': "http://localhost:9106/api/controller/"
            }
        }
