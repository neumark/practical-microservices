from .rpc import Client
client = Client()
for service in client.server_config.get_services():
    print service, client.call('ping', {}, service)
