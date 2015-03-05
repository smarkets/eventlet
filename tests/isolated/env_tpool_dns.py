from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False

if __name__ == '__main__':
    import os
    os.environ['EVENTLET_TPOOL_DNS'] = 'yes'
    from eventlet.green import socket
    socket.gethostbyname('localhost')
    socket.getaddrinfo('localhost', 80)
    print('pass')
