import threading
import socket
import cPickle as pickle
from errno import EAGAIN

def _get_and_call(object, method, *arguments):
        try:
            m = getattr(object, method)
            return_value = m(*arguments)
        except Exception as e:
            return_value = e
        return return_value

class _accept_thread(threading.Thread):
    def __init__(self, rpc, connection):
        threading.Thread.__init__(self)
        self.incoming_socket = connection[0]
        self.incoming_address = connection[1]
        self.rpc = rpc

    def run(self):
        TRYAGAIN = True
        while TRYAGAIN:
            try:
                incoming_string = self.incoming_socket.recv(10000)
                TRYAGAIN = False
            except Exception as e:
                if e[0] == EAGAIN:
                    # this is a workaround to a OS X specific bug where you
                    # need to explicitly handle EAGAIN
                    continue
                raise e

        try:
            m, arguments = pickle.loads(incoming_string)
        except EOFError:
            raise socket.error

        try:
            return_value = _get_and_call(self.rpc, m, *arguments)
            self.incoming_socket.sendall(pickle.dumps(return_value))
        except socket.error:
            # Q: why do we simply pass here?
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
            self.socket.sendall(pickle.dumps(self.message))
            data = self.socket.recv(10024)
            self.socket.close()
            self.queue.put(pickle.loads(data))
        except socket.timeout:
            self.queue.put(socket.timeout)
        except socket.error as (errno, msg):
            if errno != 4:
                self.queue.put(socket.error)
        except ValueError:
            print "Data:" + str(data)
            print "Message: "+str(self.message)
        finally:
            if self.socket:
                self.socket.close()
