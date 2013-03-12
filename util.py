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

# for threads that loop forever, but some times need to be stopped
# NB that the stop method obviously only works if the thread isn't blocked
class StoppableThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True

    def stop(self):
        self.running = False

