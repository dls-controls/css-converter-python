import pkg_resources
pkg_resources.require('dls_css_utils')
pkg_resources.require('dls_epicsparser')
pkg_resources.require('mock')

import os
import mock
import unittest
from convert import module
from dls_css_utils import coordinates


class ModuleTest(unittest.TestCase):

    def setUp(self):
        self.version = '5-3'
        self.module_path = '/dls_sw/prod/R3.14.12.3/ioc/LI/TI/'
        self.edl_path = 'MyApp/opi/edl'
        self.opi_path = 'MyApp/opi/opi'
        self.coords = coordinates.from_path2(os.path.join(self.module_path,
                                                          self.version))
        self.mirror_root = '/tmp/mirror'
        self.dummy_cfg = mock.MagicMock(
            edl_dir=self.edl_path,
            opi_dir=self.opi_path,
            path_dirs=[],
            extra_deps=[],
            groups=[],
            layers=[],
            has_opi=True)

        # Avoid checking that the directory exists
        with mock.patch('os.path.exists') as mp:
            mp.return_value = True
            self.m = module.Module(self.coords, self.dummy_cfg, self.mirror_root)

    def test_constructor_throws_ValueError_if_module_does_not_exist(self):
        dud_path = coordinates.from_path2('/dls_sw/prod/R3.14.12.3/ioc/dummy/1-1')
        self.assertRaises(ValueError, module.Module, dud_path, self.dummy_cfg, self.mirror_root)

    def test_get_dependencies(self):
        """
        Depends on self.coords existing in prod.
        """
        deps = self.m.get_dependencies()
        self.assertIsInstance(deps, dict)
        self.assertNotIn(self.m.coords.module, deps)
        self.assertNotIn(self.m.coords, deps.values())

    def test_get_edl_path(self):
        edl_path = os.path.join(self.mirror_root,
                                self.module_path[1:],
                                self.version,
                                self.edl_path)
        self.assertEqual(os.path.normpath(edl_path), self.m.get_edl_path())

    def test_get_opi_path(self):
        opi_path = os.path.join(self.mirror_root,
                                self.module_path[1:],
                                self.version,
                                self.opi_path)
        self.assertEqual(os.path.normpath(opi_path), self.m.get_opi_path())

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
