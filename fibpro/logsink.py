from rpc import Server

class LogSink(Server):
    pass

app = LogSink().app()
