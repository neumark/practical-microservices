from fibpro.rpc import Server

class ComputeWorkerServer(Server):
    NAME = "compute_worker"
    LOG_RPC = True

    def compute_fib(self, requested_fib):
        a, b = 0, 1
        for i in range(requested_fib):
            a, b = b, a + b
        return a
