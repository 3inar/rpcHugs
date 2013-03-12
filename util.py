import subprocess
import threading
from sys import platform
from socket import gethostbyname, gethostname

def get_host():
    if platform == "darwin":
        host = gethostbyname(gethostname())
    elif platform == "linux2":
        process = subprocess.Popen(["hostname", "-i"], stdout=subprocess.PIPE)
        hosts = process.communicate()[0].strip()
        hosts = hosts.split()
        if len(hosts) > 0:
            host = hosts[0]
        else:
            host = gethostbyname(gethostname())
    return str(host)

class StoppableThread(threading.Thread):
    """
    Class stub implementing the stop method. This can be
    inherited by all threads that need to be explicitely
    stoppable, that is, all threads with a while true loop.
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True

    def stop(self):
        self.running = False

