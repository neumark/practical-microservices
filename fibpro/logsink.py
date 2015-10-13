from rpc import Client, Server, ServerConfig, get_threadlocal
from logging import getLogger

class LogSinkBase(object):
    NAME = "logsink"

class LogSinkServer(LogSinkBase, Server):

    log = getLogger('gunicorn.error')

    # runs in the logsink process
    def recv_log(self, message=None, level='info'):
        if message:
            source = getattr(get_threadlocal(), "request_meta", {}).get('source', 'unknown')
            getattr(self.log, level)(
                "[%s] %s" % (source, message))
            return True
        return False

class LogSinkClient(LogSinkBase, Client):
    # runs in the client process
    def send_log(self, message, level='info'):
        return self.call('recv_log', {
            'message': message,
            'level': level})

    # convenience functions            
    def info(self, message):
        return self.send_log(message)

    def warn(self, message):
        return self.send_log(message, 'warn')

    def error(self, message):
        return self.send_log(message, 'error')

log = LogSinkClient()
