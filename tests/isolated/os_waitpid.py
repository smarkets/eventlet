from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False

if __name__ == '__main__':
    import subprocess
    import eventlet
    eventlet.monkey_patch(all=False, os=True)
    process = subprocess.Popen("sleep 0.1 && false", shell=True)
    rc = process.wait()
    assert rc == 1, rc
    print('pass')
