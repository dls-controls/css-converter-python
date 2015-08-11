
from convert.utils import parse_module_name, increment_version, get_all_dirs, \
    find_modules

import unittest


class UtilsTest(unittest.TestCase):

    def test_parse_module_name_module_only(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/prod/R3.14.12.3/support')
        self.assertEquals(module, 'diagOpi')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_only_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/support')
        self.assertEquals(module, 'motor')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_full_path_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/RF/data/SR-RF-Overview.edl'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/support')
        self.assertEquals(module, 'RF')
        self.assertIsNone(version)
        self.assertEquals(rel_path, 'data/SR-RF-Overview.edl')

    def test_parse_module_name_module_and_version(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/ACRSrc/Makefile'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, 'motorApp/ACRSrc/Makefile')

    def test_parse_module_name_module_version_directory(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, 'motorApp')

    def test_parse_module_name_nested_module(self):
        path = '/dls_sw/prod/R3.14.12.3/ioc/ME09C/ME09C-EA-IOC-01/1-3'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/prod/R3.14.12.3/ioc')
        self.assertEquals(module, 'ME09C/ME09C-EA-IOC-01')
        self.assertEquals(version, '1-3')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path_diag(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-44/booster/waveform.edl'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'diagOpi')
        self.assertEquals(version, '2-44')
        self.assertEquals(rel_path, 'booster/waveform.edl')

    def test_parse_module_name_module_and_version_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/6-7-1dls8'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_launcher(self):
        path = '/dls_sw/prod/etc/Launcher'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module_path, path)
        self.assertEquals(module, '')
        self.assertEquals(version, '')
        self.assertEquals(rel_path, '')

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
        module_path, module, version, rel_path = parse_module_name(path)
        os.path.realpath = old_realpath
        self.assertEquals(module, 'BudkerSCMPW')
        self.assertEquals(module_path, '/dls_sw/prod/R3.14.12.3/support')
        self.assertEquals(version, '1-7')
        self.assertEquals(rel_path, 'data/SCMPW.sh')

    @unittest.expectedFailure
    def test_parse_module_name_CS_CS_in_work(self):
        """
        This test fails because I can't think of a way of
        providing this functionality.
        """
        path = '/dls_sw/work/R3.14.12.3/ioc/CS/CS-TI-IOC-01/data'
        module_path, module, version, rel_path = parse_module_name(path)
        self.assertEquals(module, 'CS/CS-TI-IOC-01')
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/ioc')
        self.assertEquals(version, None)
        self.assertEquals(rel_path, 'data')


class TestIncrementVersion(unittest.TestCase):

    def test_handles_basic_cases(self):
        old_versions = ['0-1', '0-2', '1-2', '11-12']
        new_versions = ['0-2', '0-3', '1-3', '11-13']
        for old, new in zip(old_versions, new_versions):
            self.assertEqual(new, increment_version(old))

    def test_correctly_increments_nineteen(self):
        old = '3-19'
        new = '3-20'
        self.assertEqual(new, increment_version(old))

    def test_handles_periods(self):
        old_versions = ['0.1', '11.12']
        new_versions = ['0.2', '11.13']
        for old, new in zip(old_versions, new_versions):
            self.assertEqual(new, increment_version(old))

    def test_handles_dls_versions(self):
        old = '3-4-2dls3'
        new = '3-4-2dls4'
        self.assertEqual(new, increment_version(old))

    def test_returns_unchanged_version_if_does_not_end_with_number(self):
        version = '1-4dls-alpha'

        self.assertEqual(version, increment_version(version))


class TestGetModules(unittest.TestCase):

    def test_find_modules_returns_module_names_in_ioc_LI(self):
        modules = find_modules("/dls_sw/prod/R3.14.12.3/ioc/LI")
        expected_modules = [
            'LI/LI-DI-IOC-01', 'LI/LI-DI-IOC-02', 'LI/LI-PC-IOC-01',
            'LI/LI-PC-IOC-02', 'LI/PS', 'LI/RF', 'LI/TI', 'LI/VA']

        self.assertSetEqual(set(expected_modules), set(modules))

    def test_find_modules_returns_module_names_in_support_vacuum(self):
        modules = find_modules("/dls_sw/prod/R3.14.12.3/support/vacuum")
        expected_modules = ['vacuum']

        self.assertSetEqual(set(expected_modules), set(modules))


if __name__ == '__main__':
    unittest.main()
