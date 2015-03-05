from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    from eventlet import patcher
    patcher.monkey_patch()
    from eventlet import tpool
    state = []
    tpool.execute(state.append, 1)
    tpool.execute(state.append, 2)
    tpool.killall()
    assert set(state) == set([1, 2])
    print('pass')

if __name__ == '__main__':
    main()
