import pkg_resources
pkg_resources.require('dls_epicsparser')
import os
import unittest
from convert import module
from convert import coordinates


class ModuleTest(unittest.TestCase):

    def setUp(self):
        self.coords = coordinates.from_path2('/dls_sw/prod/R3.14.12.3/ioc/LI/TI/5-3')
        print('The coordinates are {}'.format(self.coords))
        self.mirror_root = '/tmp/mirror'
        dummy_cfg = {'edl_dir': '.',
                     'opi_dir': '.',
                     'extra_deps': []}
        self.m = module.Module(self.coords, dummy_cfg, self.mirror_root)

    def test_get_dependencies(self):
        """
        Depends on self.coords existing in prod.
        """
        deps = self.m.get_dependencies()
        self.assertIsInstance(deps, dict)
        self.assertNotIn(self.m.coords.module, deps)
        self.assertNotIn(self.m.coords, deps.values())

    def test_get_edl_path(self):
        """
        This is just turning the method inside-out.
        """
        edl_path = os.path.join(self.m.mirror_root, self.m.new_module_dir[1:],
                                self.m.edl_dir)
        self.assertEqual(os.path.normpath(edl_path), self.m.get_edl_path())

    def test_convert(self):
        """
        Not yet implemented.
        """
        pass


class ConvertAllTest(unittest.TestCase):

    def test_convert_all(self):
        """
        Not yet implemented.
        """
        pass


if __name__ == '__main__':
    unittest.main()
