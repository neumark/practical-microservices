from const import HOSTNAME

client_constructors = {}

def get_default_endpoints():
    return {
        'logsink': "http://{}/api/logsink/".format(HOSTNAME),
        'userstore': "http://{}/api/userstore/".format(HOSTNAME),
        'compute': "http://{}/api/compute/".format(HOSTNAME),
        'pricing': "http://{}/api/pricing/".format(HOSTNAME)}

def register_client_constructor(service, constructor):
    client_constructors[service] = constructor

def get_client_constructor(service):
    return client_constructors.get(service)
