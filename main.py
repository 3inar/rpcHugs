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

    def __repr__(self):
        return "<remote RPC module at " + self.proxy[0] +":" + str(self.proxy[1]) + ">"

    def __str__(self):
        return self.proxy[0] +":" + str(self.proxy[1])
        
    def __getattr__(self, name):
        # I'm to this day uncertain how this works, just run with it man
        def get(_name, *args):
            return self.rpc.call(self.proxy, _name, *args)
        return get.__get__(name)

class RPC:
    def __init__(self, port=0):
        self.server = ServerStub(self, port)
        self.server.start()

    def is_alive(self):
        return self.server.is_alive()

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

        if issubclass(ret.__class__, Exception):
            raise ret
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
        except Exception as e:
            print "RPC server stub could not open socket:"
            print e
            exit(1)

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
                except socket.error as e:
                    # Q: why do we simply pass here?
                    print e
                    pass
        self.socket.close()

# demo of how to rpc:
class _testRpc(RPC):
    def __init__(self, port=0):
        RPC.__init__(self, port)

    def add(self, a, b):
        return a + b

if __name__ == "__main__":
    try:
        import sys
    
        # the callee doesn't have to be of same derived class as caller
        caller_rpc = _testRpc()
        callee_rpc = _testRpc()

        remote_address = callee_rpc.server_info()
        callee = Dummy(caller_rpc, remote_address)

        num_tests = 10000
        print 'adding two numbers ' + str(num_tests) + ' times via RPC'
        for i in range(num_tests):
            value = callee.add(i, i**2)
            sys.stdout.write('\r' + str(int(i*100.0/num_tests)) + ' %')
        sys.stdout.write('\rDONE       \n')
        sys.stdout.flush()
    except:
        sys.stdout.write('\n')
        sys.stdout.flush()
        raise
    finally:
        # NB that if you DON'T handle exceptions in the RPC thing like this,
        # an exception will cause you to wait for the server stub forever
        # (unless the server stub was the thread that died, but that is not
        # what usually happens)
        caller_rpc.shutdown()
        callee_rpc.shutdown()

