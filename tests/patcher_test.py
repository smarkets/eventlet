import os
import shutil
import sys
import tempfile

from eventlet.support import six
import tests


base_module_contents = """
import socket
import urllib
print("base {0} {1}".format(socket, urllib))
"""

patching_module_contents = """
from eventlet.green import socket
from eventlet.green import urllib
from eventlet import patcher
print('patcher {0} {1}'.format(socket, urllib))
patcher.inject('base', globals(), ('socket', socket), ('urllib', urllib))
del patcher
"""

import_module_contents = """
import patching
import socket
print("importing {0} {1} {2} {3}".format(patching, socket, patching.socket, patching.urllib))
"""


class ProcessBase(tests.LimitedTestCase):
    TEST_TIMEOUT = 3  # starting processes is time-consuming

    def setUp(self):
        super(ProcessBase, self).setUp()
        self._saved_syspath = sys.path
        self.tempdir = tempfile.mkdtemp('_patcher_test')

    def tearDown(self):
        super(ProcessBase, self).tearDown()
        sys.path = self._saved_syspath
        shutil.rmtree(self.tempdir)

    def write_to_tempfile(self, name, contents):
        filename = os.path.join(self.tempdir, name)
        if not filename.endswith('.py'):
            filename = filename + '.py'
        with open(filename, "w") as fd:
            fd.write(contents)

    def launch_subprocess(self, filename):
        path = os.path.join(self.tempdir, filename)
        output = tests.run_python(path)
        if six.PY3:
            output = output.decode('utf-8')
            separator = '\n'
        else:
            separator = b'\n'
        lines = output.split(separator)
        return output, lines


class ImportPatched(ProcessBase):
    def test_patch_a_module(self):
        self.write_to_tempfile("base", base_module_contents)
        self.write_to_tempfile("patching", patching_module_contents)
        self.write_to_tempfile("importing", import_module_contents)
        output, lines = self.launch_subprocess('importing.py')
        assert lines[0].startswith('patcher'), repr(output)
        assert lines[1].startswith('base'), repr(output)
        assert lines[2].startswith('importing'), repr(output)
        assert 'eventlet.green.socket' in lines[1], repr(output)
        assert 'eventlet.green.urllib' in lines[1], repr(output)
        assert 'eventlet.green.socket' in lines[2], repr(output)
        assert 'eventlet.green.urllib' in lines[2], repr(output)
        assert 'eventlet.green.httplib' not in lines[2], repr(output)

    def test_import_patched_defaults(self):
        self.write_to_tempfile("base", """
import socket
try:
    import urllib.request as urllib
except ImportError:
    import urllib
print("base {0} {1}".format(socket, urllib))""")

        new_mod = """
from eventlet import patcher
base = patcher.import_patched('base')
print("newmod {0} {1} {2}".format(base, base.socket, base.urllib.socket.socket))
"""
        self.write_to_tempfile("newmod", new_mod)
        output, lines = self.launch_subprocess('newmod.py')
        assert lines[0].startswith('base'), repr(output)
        assert lines[1].startswith('newmod'), repr(output)
        assert 'eventlet.green.socket' in lines[1], repr(output)
        assert 'GreenSocket' in lines[1], repr(output)


class MonkeyPatch(ProcessBase):
    def test_patched_modules(self):
        new_mod = """
from eventlet import patcher
patcher.monkey_patch()
import socket
try:
    import urllib.request as urllib
except ImportError:
    import urllib
print("newmod {0} {1}".format(socket.socket, urllib.socket.socket))
"""
        self.write_to_tempfile("newmod", new_mod)
        output, lines = self.launch_subprocess('newmod.py')
        assert lines[0].startswith('newmod'), repr(output)
        self.assertEqual(lines[0].count('GreenSocket'), 2, repr(output))

    def test_early_patching(self):
        new_mod = """
from eventlet import patcher
patcher.monkey_patch()
import eventlet
eventlet.sleep(0.01)
print("newmod")
"""
        self.write_to_tempfile("newmod", new_mod)
        output, lines = self.launch_subprocess('newmod.py')
        self.assertEqual(len(lines), 2, repr(output))
        assert lines[0].startswith('newmod'), repr(output)

    def test_late_patching(self):
        new_mod = """
import eventlet
eventlet.sleep(0.01)
from eventlet import patcher
patcher.monkey_patch()
eventlet.sleep(0.01)
print("newmod")
"""
        self.write_to_tempfile("newmod", new_mod)
        output, lines = self.launch_subprocess('newmod.py')
        self.assertEqual(len(lines), 2, repr(output))
        assert lines[0].startswith('newmod'), repr(output)

    def assert_boolean_logic(self, call, expected, not_expected=''):
        expected_list = ", ".join(['"%s"' % x for x in expected.split(',') if len(x)])
        not_expected_list = ", ".join(['"%s"' % x for x in not_expected.split(',') if len(x)])
        new_mod = """
from eventlet import patcher
%s
for mod in [%s]:
    assert patcher.is_monkey_patched(mod), mod
for mod in [%s]:
    assert not patcher.is_monkey_patched(mod), mod
print("already_patched {0}".format(",".join(sorted(patcher.already_patched.keys()))))
""" % (call, expected_list, not_expected_list)
        self.write_to_tempfile("newmod", new_mod)
        output, lines = self.launch_subprocess('newmod.py')
        ap = 'already_patched'
        assert lines[0].startswith(ap), repr(output)
        patched_modules = lines[0][len(ap):].strip()
        # psycopg might or might not be patched based on installed modules
        patched_modules = patched_modules.replace("psycopg,", "")
        # ditto for MySQLdb
        patched_modules = patched_modules.replace("MySQLdb,", "")
        self.assertEqual(
            patched_modules, expected,
            "Logic:%s\nExpected: %s != %s" % (call, expected, patched_modules))

    def test_boolean(self):
        self.assert_boolean_logic("patcher.monkey_patch()",
                                  'os,select,socket,thread,time')

    def test_boolean_all(self):
        self.assert_boolean_logic("patcher.monkey_patch(all=True)",
                                  'os,select,socket,thread,time')

    def test_boolean_all_single(self):
        self.assert_boolean_logic("patcher.monkey_patch(all=True, socket=True)",
                                  'os,select,socket,thread,time')

    def test_boolean_all_negative(self):
        self.assert_boolean_logic(
            "patcher.monkey_patch(all=False, socket=False, select=True)",
            'select')

    def test_boolean_single(self):
        self.assert_boolean_logic("patcher.monkey_patch(socket=True)",
                                  'socket')

    def test_boolean_double(self):
        self.assert_boolean_logic("patcher.monkey_patch(socket=True, select=True)",
                                  'select,socket')

    def test_boolean_negative(self):
        self.assert_boolean_logic("patcher.monkey_patch(socket=False)",
                                  'os,select,thread,time')

    def test_boolean_negative2(self):
        self.assert_boolean_logic("patcher.monkey_patch(socket=False, time=False)",
                                  'os,select,thread')

    def test_conflicting_specifications(self):
        self.assert_boolean_logic("patcher.monkey_patch(socket=False, select=True)",
                                  'select')


def test_tpool_original_thread():
    tests.run_isolated('patcher_tpool_original_thread.py')


def test_tpool_patched_thread():
    tests.run_isolated('patcher_tpool_patched_thread.py')


def test_tpool_simple():
    tests.run_isolated('patcher_tpool_simple.py')


def test_subprocess():
    tests.run_isolated('patcher_subprocess.py')


def test_threading_original_thread():
    tests.run_isolated('patcher_threading_original_thread.py')


def test_threading_patched_thread():
    tests.run_isolated('patcher_threading_patched_thread.py')


def test_threading_tpool():
    tests.run_isolated('patcher_threading_tpool.py')


def test_threading_greenlet():
    tests.run_isolated('patcher_threading_greenlet.py')


def test_threading_greenthread():
    tests.run_isolated('patcher_threading_greenthread.py')


def test_monkey_patch_ok():
    tests.run_isolated('patcher_monkey_patch_ok.py')


def test_monkey_patch_unknown_module():
    tests.run_isolated('patcher_monkey_patch_unknown_module.py')


def test_os_waitpid():
    tests.run_isolated('os_waitpid.py')


class GreenThreadWrapper(ProcessBase):
    prologue = """import eventlet
eventlet.monkey_patch()
import threading
def test():
    t = threading.currentThread()
"""
    epilogue = """
t = eventlet.spawn(test)
t.wait()
"""

    def test_join(self):
        self.write_to_tempfile("newmod", self.prologue + """
    def test2():
        global t2
        t2 = threading.currentThread()
    eventlet.spawn(test2)
""" + self.epilogue + """
print(repr(t2))
t2.join()
""")
        output, lines = self.launch_subprocess('newmod')
        self.assertEqual(len(lines), 2, "\n".join(lines))
        assert lines[0].startswith('<_GreenThread'), lines[0]

    def test_name(self):
        self.write_to_tempfile("newmod", self.prologue + """
    print(t.name)
    print(t.getName())
    print(t.get_name())
    t.name = 'foo'
    print(t.name)
    print(t.getName())
    print(t.get_name())
    t.setName('bar')
    print(t.name)
    print(t.getName())
    print(t.get_name())
""" + self.epilogue)
        output, lines = self.launch_subprocess('newmod')
        self.assertEqual(len(lines), 10, "\n".join(lines))
        for i in range(0, 3):
            self.assertEqual(lines[i], "GreenThread-1", lines[i])
        for i in range(3, 6):
            self.assertEqual(lines[i], "foo", lines[i])
        for i in range(6, 9):
            self.assertEqual(lines[i], "bar", lines[i])

    def test_ident(self):
        self.write_to_tempfile("newmod", self.prologue + """
    print(id(t._g))
    print(t.ident)
""" + self.epilogue)
        output, lines = self.launch_subprocess('newmod')
        self.assertEqual(len(lines), 3, "\n".join(lines))
        self.assertEqual(lines[0], lines[1])

    def test_is_alive(self):
        self.write_to_tempfile("newmod", self.prologue + """
    print(t.is_alive())
    print(t.isAlive())
""" + self.epilogue)
        output, lines = self.launch_subprocess('newmod')
        self.assertEqual(len(lines), 3, "\n".join(lines))
        self.assertEqual(lines[0], "True", lines[0])
        self.assertEqual(lines[1], "True", lines[1])

    def test_is_daemon(self):
        self.write_to_tempfile("newmod", self.prologue + """
    print(t.is_daemon())
    print(t.isDaemon())
""" + self.epilogue)
        output, lines = self.launch_subprocess('newmod')
        self.assertEqual(len(lines), 3, "\n".join(lines))
        self.assertEqual(lines[0], "True", lines[0])
        self.assertEqual(lines[1], "True", lines[1])


def test_importlib_lock():
    tests.run_isolated('patcher_importlib_lock.py')


def test_psycopg_patched():
    tests.run_isolated('patcher_psycopg.py')
