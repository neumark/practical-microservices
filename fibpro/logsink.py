from rpc import Client, Server, ServerConfig, get_threadlocal, get_request_meta
from logging import getLogger

class LogSinkBase(object):
    NAME = "logsink"

class LogSinkServer(LogSinkBase, Server):

    log = getLogger('gunicorn.error')

    def recv_log(self, message=None, level='info'):
        if message:
            source = get_request_meta().get('source', 'unknown')
            request_id = get_request_meta().get('request_id') or '-'
            getattr(self.log, level)(
                "[%s] %s %s" % (source, request_id, message))
            return True
        return False

class LogSinkClient(LogSinkBase, Client):
    
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
