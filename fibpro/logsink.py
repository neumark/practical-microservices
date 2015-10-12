from rpc import Client, Server, ServerConfig
from logging import getLogger


class LogSinkServer(Server):

    log = getLogger('gunicorn.error')

    # runs in the logsink process
    def recv_log(self, message=None, level='info'):
        if message:
            getattr(self.log, level)(message)
            return True
        return False

class LogSinkClient(Client):
    # runs in the client process
    def send_log(self, message, level='info'):
        return self.call('logsink', 'recv_log', {
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
