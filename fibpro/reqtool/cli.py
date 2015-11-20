from wsgi_intercept import requests_intercept, add_wsgi_intercept
from wsgi_proxy import WSGIProxyApplication 
from fibpro.userstore import UserStoreServer, UserStoreClient

from fibpro.reqtool.record import RecordingProxy

def intercept(host, port, app):
    add_wsgi_intercept(host, port, lambda: app)

requests_intercept.install()
proxy = RecordingProxy(UserStoreServer(register=False).app())
#proxy = RecordingProxy(WSGIProxyApplication())
intercept('127.0.0.1', 9003, proxy)
UserStoreClient().get_user("username")
print proxy.session[0][0].__dict__
print proxy.session[0][1].__dict__
