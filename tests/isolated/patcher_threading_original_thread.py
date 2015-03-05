from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    import eventlet
    eventlet.monkey_patch()
    import threading
    threading_original = eventlet.patcher.original('threading')
    state = ['']

    def fun():
        state[0] = repr(threading.currentThread())

    t = threading_original.Thread(target=fun)
    t.start()
    t.join()

    assert state[0].startswith('<Thread'), state[0]
    active_patched = len(threading._active)
    active_original = len(threading_original._active)
    assert active_patched == 1, active_patched
    assert active_original == 1, active_original
    print('pass')

if __name__ == '__main__':
    main()
