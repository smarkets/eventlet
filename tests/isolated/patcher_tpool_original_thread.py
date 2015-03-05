from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    import eventlet
    eventlet.monkey_patch(time=False, thread=False)
    from eventlet import tpool
    import time

    tickcount = [0]

    def tick():
        from eventlet.support import six
        for i in six.moves.range(1000):
            tickcount[0] += 1
            eventlet.sleep()

    def do_sleep():
        tpool.execute(time.sleep, 0.5)

    eventlet.spawn(tick)
    w1 = eventlet.spawn(do_sleep)
    w1.wait()
    assert tickcount[0] > 900
    tpool.killall()
    print('pass')

if __name__ == '__main__':
    main()
