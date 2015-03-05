from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    from tests.db_pool_test import postgres_requirement
    if not postgres_requirement(None, debug=False):
        print('skip:postgres_requirement')
        return

    import sys
    import eventlet
    eventlet.monkey_patch()
    if not eventlet.patcher.is_monkey_patched('psycopg'):
        print('psycopg not monkeypatched')
        sys.exit(1)

    from eventlet.support import six
    import tests
    # construct a non-json dsn for the subprocess
    psycopg_auth = tests.get_database_auth()['psycopg2']
    if isinstance(psycopg_auth, six.string_types):
        dsn = psycopg_auth
    else:
        dsn = " ".join(["%s=%s" % (k, v) for k, v in six.iteritems(psycopg_auth)])

    count = [0]

    def tick(totalseconds, persecond):
        for i in range(totalseconds * persecond):
            count[0] += 1
            eventlet.sleep(1.0 / persecond)

    import psycopg2

    def fetch(num, secs):
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        for i in range(num):
            cur.execute("select pg_sleep(%s)", [secs])

    f = eventlet.spawn(fetch, 2, 1)
    eventlet.spawn(tick, 2, 100)
    f.wait()
    assert count[0] > 100, count[0]
    print('pass')

if __name__ == '__main__':
    main()
