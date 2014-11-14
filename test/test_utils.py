
from convert.utils import parse_module_name

import unittest


class UtilsTest(unittest.TestCase):

    def test_parse_module_name_module_only(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'diagOpi')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_only_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_and_version(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/ACRSrc/Makefile'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, 'motorApp/ACRSrc/Makefile')

    def test_parse_module_name_nested_module(self):
        path = '/dls_sw/prod/R3.14.12.3/ioc/ME09C/ME09C-EA-IOC-01/1-3'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'ME09C/ME09C-EA-IOC-01')
        self.assertEquals(version, '1-3')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path_diag(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-44/booster/waveform.edl'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'diagOpi')
        self.assertEquals(version, '2-44')
        self.assertEquals(rel_path, 'booster/waveform.edl')

    def test_parse_module_name_module_and_version_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/6-7-1dls8'
        module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_launcher(self):
        path = '/dls_sw/prod/etc/Launcher'
        self.assertRaises(ValueError, parse_module_name, path)

    def test_parse_module_name_no_module(self):
        path = '/dls_sw/prod/R3.14.12.3/support/'
        self.assertRaises(ValueError, parse_module_name, path)

    def test_parse_module_name_module_version_Rxy(self):
        path = '/dls_sw/prod/R3.14.12.3/support/BudkerSCMPW/Rx-y/data/SCMPW.sh'
        def mock_realpath(path):
            return '/dls_sw/prod/R3.14.12.3/support/BudkerSCMPW/1-7/data/SCMPW.sh'
        import os
        old_realpath = os.path.realpath
        os.path.realpath = mock_realpath
        module, version, rel_path = parse_module_name(path)
        os.path.realpath = old_realpath
        self.assertEquals(module, 'BudkerSCMPW')
        self.assertEquals(version, '1-7')
        self.assertEquals(rel_path, 'data/SCMPW.sh')

if __name__ == '__main__':
    unittest.main()
