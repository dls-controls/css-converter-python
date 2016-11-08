import pkg_resources
pkg_resources.require('dls_css_utils')
from convert.launcher import _get_macros, LauncherCommand
import unittest


class LauncherTest(unittest.TestCase):

    def test_get_macros_with_none(self):
        args = ['a', 'b', 'c']
        macros = _get_macros(args)
        self.assertEquals(macros, {})

    def test_get_macros_with_one_macro(self):
        args = ['-m', 'x=y']
        macros = _get_macros(args)
        self.assertEquals(macros, {'x': 'y'})

    def test_get_macros_with_two_macros(self):
        args = ['-m', 'x=y,a=b']
        macros = _get_macros(args)
        self.assertEquals(macros, {'x': 'y', 'a': 'b'})

    def test_get_macros_with_incorrect_args(self):
        args = ['-m']
        macros = _get_macros(args)
        self.assertEquals(macros, {})


class LauncherCommandTest(unittest.TestCase):

    def test_cmds_compare_equal(self):
        cmd1 = LauncherCommand("a", "b", "c")
        cmd2 = LauncherCommand("a", "b", "c")
        self.assertEqual(cmd1, cmd2)

    def test_cmds_hash_equal(self):
        cmd1 = LauncherCommand("a", "b", "c")
        cmd2 = LauncherCommand("a", "b", "c")
        d = {}
        d[cmd1] = "a"
        d[cmd2] = "b"
        self.assertEqual(d[cmd1], "b")
        self.assertEqual(len(d), 1)

if __name__ == '__main__':
    unittest.main()
