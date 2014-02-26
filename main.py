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

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __hash__(self):
        return hash(str(self))
        
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

    def getDummy(self, host):
        return Dummy(self, host)

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
        util.StoppableThread.__init__(self, daemon=True)
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
                    call = _accept_thread(self.rpc, s.accept())
                    call.start()
                except socket.error as e:
                    # Q: why do we simply pass here?
                    print e
                    pass
        self.socket.close()

if __name__ == '__main__':
    #testing comparison:
    try:
        rpc = RPC()
        rpc2 = RPC()

        d1 = Dummy(rpc, rpc.server_info())
        d2 = Dummy(rpc2, rpc.server_info())
        t = (d1 != d2)
        assert t == False
        t = (d1 == d2)
        assert t == True

        dct = {}
        dct[d1] = "sup bro"
        t = (d2 in dct)
        assert t == True

        rpc.shutdown()
        rpc2.shutdown()
        print "all good with the comparison tests man"
    except:
        rpc.shutdown()
        rpc2.shutdown()
        raise

