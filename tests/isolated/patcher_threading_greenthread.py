from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    import eventlet
    eventlet.monkey_patch()
    import threading
    state = ['']

    def fun():
        state[0] = repr(threading.currentThread())

    eventlet.spawn(fun).wait()
    assert state[0].startswith('<_GreenThread'), state[0]
    active_count = len(threading._active)
    assert active_count == 1, active_count
    print('pass')

if __name__ == '__main__':
    main()
