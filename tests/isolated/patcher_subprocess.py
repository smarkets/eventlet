from __future__ import print_function

# no standard tests in this file, ignore
__test__ = False


def main():
    import sys
    import eventlet
    eventlet.monkey_patch()
    from eventlet.green import subprocess

    subprocess.Popen([sys.executable, '-c', ''], stdin=subprocess.PIPE)

    print('pass')

if __name__ == '__main__':
    main()
