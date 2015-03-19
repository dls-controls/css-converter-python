from convert.launcher import _get_macros
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


if __name__ == '__main__':
    unittest.main()
