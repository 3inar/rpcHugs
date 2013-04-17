import threading
import socket
import cPickle as pickle
from errno import EAGAIN

def _recv(recv_socket):
        TRYAGAIN = True
        while TRYAGAIN:
            try:
                incoming_string = recv_socket.recv(10000)
                TRYAGAIN = False
            except Exception as e:
                if e[0] == EAGAIN:
                    # this is a workaround to a OS X specific bug where you
                    # need to explicitly handle EAGAIN
                    continue
                raise e
        return incoming_string

def _get_and_call(object, method, *arguments):
        try:
            m = getattr(object, method)
            return_value = m(*arguments)
        except Exception as e:
            return_value = e
        return return_value

class _accept_thread(threading.Thread):
    def __init__(self, rpcObject, connection):
        threading.Thread.__init__(self)
        self.incoming_socket = connection[0]
        self.incoming_address = connection[1]
        self.rpcObject = rpcObject

    def run(self):
        try:
            binary = _recv(self.incoming_socket)
            m, arguments = pickle.loads(binary)
        except EOFError:
            # Q: what's up with this exception conversion?
            # it certainly won't percolate up to the parent thread
            raise socket.error

        try:
            return_value = _get_and_call(self.rpcObject, m, *arguments)
            self.incoming_socket.sendall(pickle.dumps(return_value, 2))
        except socket.error:
            # we don't care whether or no the recipient is there for the result
            pass

class _call_thread(threading.Thread):
    def __init__(self, queue, callee, method, *args):
        threading.Thread.__init__(self)
        msec = 0.001
        self.timeout = 3000*msec
        self.callee = callee
        self.queue = queue
        self.message = (method, args)
        self.socket = None

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.callee)
            self.socket.sendall(pickle.dumps(self.message, 2))
            data = _recv(self.socket)
            self.socket.close()
            self.queue.put(pickle.loads(data))
        except Exception as e:
            self.queue.put(e)
        finally:
            if self.socket:
                self.socket.close()
