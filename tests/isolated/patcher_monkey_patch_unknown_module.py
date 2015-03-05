from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False

if __name__ == '__main__':
    import eventlet
    err = ''
    try:
        eventlet.monkey_patch(finagle=True)
    except TypeError as e:
        err = str(e)
    assert 'finagle' in err, err
    print('pass')
