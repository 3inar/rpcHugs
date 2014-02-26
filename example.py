from main import RPC, Dummy
# demo of how to rpc:


class _testRpc(RPC):
    def __init__(self, port=0):
        RPC.__init__(self, port)

    def add(self, a, b):
        return a + b

    def echo(self, val):
        return val

if __name__ == "__main__":
    try:
        import sys
    
        # the callee doesn't have to be of same derived class as caller
        caller_rpc = _testRpc()
        callee_rpc = _testRpc()

        remote_address = callee_rpc.server_info()
        callee = caller_rpc.getDummy(remote_address)

        num_tests = 100
        print 'adding two numbers ' + str(num_tests) + ' times via RPC'
        for i in range(num_tests):
            i_sq = i**2
            value = callee.add(i, i_sq)
            assert value == (i + i_sq)
            sys.stdout.write('\r' + str(int(i*100.0/num_tests)) + ' %')
        sys.stdout.write('\rDONE       \n')
        sys.stdout.flush()

        # the following can safely be out-commented if you have no PIL
        # from PIL import Image
        # image = Image.open('CLOUDS.jpg')
        # string = image.tostring("jpeg", "RGB").encode("base64")

        # callee.echo(string)
    except:
        sys.stdout.write('\n')
        sys.stdout.flush()
        raise

