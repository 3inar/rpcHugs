import sys
import socket
import select
import time
import Queue
import util
from rpcthreads import _accept_thread, _call_thread, _get_and_call

class Dummy():
    def __init__(self, rpc, proxy):
        self.proxy = tuple(proxy)
        self.rpc = rpc

    def __getattr__(self, name):
        # I'm to this day uncertain how this works, just run with it man
        def get(_name, *args):
            return self.rpc.call(self.proxy, _name, *args)
        return get.__get__(name)

class RPC:
    def __init__(self, port=0):
        self.server = ServerStub(self, port)
        self.server.start()

    def shutdown(self):
        self.server.stop()
        self.server.join()

    def server_info(self):
        return (self.server.host, self.server.port)

    def call(self, callee, method, *args):
        queue = Queue.Queue()

        if self.server_info() == callee:
            return _get_and_call(self, method, *args)

        cStub = _call_thread(queue, callee, method, *args)
        cStub.start()
        ret = queue.get()
        cStub.join()

        if ret == socket.timeout:
            raise socket.timeout
        elif ret == socket.error:
            raise socket.error
        else:
            return ret

    def echo(self, item):
        return item

class ServerStub(util.StoppableThread):
    def __init__(self, rpc, port=0, backlog=10, timeout=0.5):
        util.StoppableThread.__init__(self)
        self.socket = None
        self.backlog = backlog
        self.rpc = rpc
        self.timeout = timeout
        self.open_socket(port)

    def open_socket(self, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('', port))
            self.port = self.socket.getsockname()[1]
            self.host = util.get_host()
            self.socket.listen(self.backlog)
            self.socket.setblocking(0)
        except socket.error, (value, message):
            if self.socket:
                self.socket.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        reads = [self.socket]
        writes = []
        exceptions = []

        while self.running:
            inc, outg, exc = select.select(reads, writes, exceptions,
                                           self.timeout)
            for s in inc:
                try:
                    rpc = _accept_thread(self.rpc, s.accept())
                    rpc.start()
                except socket.error:
                    # Q: why do we simply pass here?
                    pass
        self.socket.close()

# demo of how to rpc:
class _testRpc(RPC):
    def __init__(self, port=0):
        RPC.__init__(self, port)

    def add(self, a, b):
        return a + b

if __name__ == "__main__":
    caller = _testRpc()
    callee = _testRpc()

    remote_address = callee.server_info()
    callee = Dummy(caller, remote_address)

    for i in range(10000):
        value = callee.add(i, i**2)
        print ' '.join([str(i), "+", str(i**2), "=", str(value)])

    caller.shutdown()
    callee.shutdown()
    quit()

