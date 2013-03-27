from main import RPC, Dummy
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

