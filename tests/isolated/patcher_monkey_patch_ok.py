from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False

if __name__ == '__main__':
    import eventlet
    eventlet.monkey_patch()
    print('pass')
