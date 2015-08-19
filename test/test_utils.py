import os
from pkg_resources import require
require("mock")

from mock import patch
from convert import utils


import unittest


class FileMungingTests(unittest.TestCase):

    # def test_get_all_dirs_returns_list_of_folders_ioc(self):
    #     moduledirs = utils.get_all_dirs("/dls_sw/prod/R3.14.12.3/ioc")
    #     print len(moduledirs)
    #
    # def test_get_all_dirs_returns_list_of_folders_support(self):
    #     moduledirs = utils.get_all_dirs("/dls_sw/prod/R3.14.12.3/support")
    #     print len(moduledirs)

    def test_get_all_dirs_returns_list_of_folders_support_module(self):
        moduledirs = utils.get_all_dirs("/dls_sw/prod/R3.14.12.3/support/mirror")
        for d in sorted(moduledirs):
            print d

"""
    def test_find_module_from_path_returns_path_at_module_version_from_edlfile(self):
        path = "/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3/data/mirrorKBM-I22-HFM.edl"
        expected = "/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3"

        actual = utils.find_module_from_path(path)

        self.assertEqual(expected, actual)

    def test_find_module_from_path_returns_path_at_module_version_from_deep_edlfile(self):
        path = "/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3/myIocApp/ioc/mirrorKBM-I22-HFM.edl"
        expected = "/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3"

        actual = utils.find_module_from_path(path)

        self.assertEqual(expected, actual)

    def test_find_module_from_path_returns_path_at_module_from_edlfile_no_version(self):
        path = "/dls_sw/prod/R3.14.12.3/support/mirror/data/mirrorKBM-I22-HFM.edl"
        expected = "/dls_sw/prod/R3.14.12.3/support/mirror"

        actual = utils.find_module_from_path(path)

        self.assertEqual(expected, actual)

    def test_find_module_from_path_returns_path_at_module_from_midpoint_in_tree(self):
        path = "/dls_sw/prod/R3.14.12.3/ioc/LI"
        expected = "/dls_sw/prod/R3.14.12.3/support/mirror"

        actual = utils.find_module_from_path(path)

        self.assertEqual(expected, actual)


    def test_find_module_from_path_does_something_with_versioned_support_module(self):
        path = "/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3"
        actual = utils.find_module_from_path(path)

        self.assertEqual(path, actual)


    def test_find_module_from_path_does_something_with_support_module(self):
        path = "/dls_sw/prod/R3.14.12.3/support/mirror"
        actual = utils.find_module_from_path(path)

        self.assertEqual(path, actual)

    def test_find_module_from_path_does_nothing_with_support(self):
        path = "/dls_sw/prod/R3.14.12.3/support"
        actual = utils.find_module_from_path(path)

        self.assertEqual(path, actual)
"""


class UtilsTest(unittest.TestCase):

    def test_parse_module_name_module_only(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/prod/R3.14.12.3/support')
        self.assertEquals(module, 'diagOpi')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_only_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/support')
        self.assertEquals(module, 'motor')
        self.assertIsNone(version)
        self.assertEquals(rel_path, '')

    def test_parse_module_name_full_path_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/RF/data/SR-RF-Overview.edl'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/support')
        self.assertEquals(module, 'RF')
        self.assertIsNone(version)
        self.assertEquals(rel_path, 'data/SR-RF-Overview.edl')

    def test_parse_module_name_module_and_version(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/ACRSrc/Makefile'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, 'motorApp/ACRSrc/Makefile')

    def test_parse_module_name_module_version_directory(self):
        path = '/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, 'motorApp')

    def test_parse_module_name_nested_module(self):
        path = '/dls_sw/prod/R3.14.12.3/ioc/ME09C/ME09C-EA-IOC-01/1-3'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module_path, '/dls_sw/prod/R3.14.12.3/ioc')
        self.assertEquals(module, 'ME09C/ME09C-EA-IOC-01')
        self.assertEquals(version, '1-3')
        self.assertEquals(rel_path, '')

    def test_parse_module_name_module_version_path_diag(self):
        path = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-44/booster/waveform.edl'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'diagOpi')
        self.assertEquals(version, '2-44')
        self.assertEquals(rel_path, 'booster/waveform.edl')

    def test_parse_module_name_module_and_version_in_work(self):
        path = '/dls_sw/work/R3.14.12.3/support/motor/6-7-1dls8'
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'motor')
        self.assertEquals(version, '6-7-1dls8')
        self.assertEquals(rel_path, '')

    def test_parse_module_launcher(self):
        path = '/dls_sw/prod/etc/Launcher'
        self.assertRaises(ValueError, utils.parse_module_name, path)

    def test_parse_module_name_no_module(self):
        path = '/dls_sw/prod/R3.14.12.3/support/'
        self.assertRaises(ValueError, utils.parse_module_name, path)

    def test_parse_module_name_module_version_Rxy(self):
        path = '/dls_sw/prod/R3.14.12.3/support/BudkerSCMPW/Rx-y/data/SCMPW.sh'

        def mock_realpath(path):
            return '/dls_sw/prod/R3.14.12.3/support/BudkerSCMPW/1-7/data/SCMPW.sh'

        import os
        old_realpath = os.path.realpath
        os.path.realpath = mock_realpath
        module_path, module, version, rel_path = utils.parse_module_name(path)
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
        module_path, module, version, rel_path = utils.parse_module_name(path)
        self.assertEquals(module, 'CS/CS-TI-IOC-01')
        self.assertEquals(module_path, '/dls_sw/work/R3.14.12.3/ioc')
        self.assertEquals(version, None)
        self.assertEquals(rel_path, 'data')


class TestIncrementVersion(unittest.TestCase):

    def test_handles_basic_cases(self):
        old_versions = ['0-1', '0-2', '1-2', '11-12']
        new_versions = ['0-2', '0-3', '1-3', '11-13']
        for old, new in zip(old_versions, new_versions):
            self.assertEqual(new, utils.increment_version(old))

    def test_correctly_increments_nineteen(self):
        old = '3-19'
        new = '3-20'
        self.assertEqual(new, utils.increment_version(old))

    def test_handles_periods(self):
        old_versions = ['0.1', '11.12']
        new_versions = ['0.2', '11.13']
        for old, new in zip(old_versions, new_versions):
            self.assertEqual(new, utils.increment_version(old))

    def test_handles_dls_versions(self):
        old = '3-4-2dls3'
        new = '3-4-2dls4'
        self.assertEqual(new, utils.increment_version(old))

    def test_returns_unchanged_version_if_does_not_end_with_number(self):
        version = '1-4dls-alpha'

        self.assertEqual(version, utils.increment_version(version))


class TestGetModules(unittest.TestCase):

    def test_find_modules_returns_module_names_in_ioc_LI(self):
        modules = utils.find_modules("/dls_sw/prod/R3.14.12.3/ioc/LI")
        expected_modules = [
            'LI/LI-DI-IOC-01', 'LI/LI-DI-IOC-02', 'LI/LI-PC-IOC-01',
            'LI/LI-PC-IOC-02', 'LI/PS', 'LI/RF', 'LI/TI', 'LI/VA']
        self.assertListEqual(sorted(expected_modules), sorted(modules))

    def test_find_modules_returns_module_names_in_support_vacuum(self):
        modules = utils.find_modules("/dls_sw/prod/R3.14.12.3/support/vacuum")
        expected_modules = ['vacuum']
        self.assertListEqual(expected_modules, modules)

    def test_find_modules_returns_empty_list_if_path_does_not_exist(self):
        modules = utils.find_modules("/dummy/path")
        expected_modules = []
        self.assertListEqual(expected_modules, modules)

    def test_parse_version_handles_pair_case(self):
        self.assertListEqual([4,2], utils.parse_version("4-2"))

    def test_parse_version_handles_triple_case(self):
        self.assertListEqual([4,2,1], utils.parse_version("4-2-1"))

    def test_parse_version_handles_pair_case_with_unnumbered_suffix(self):
        self.assertListEqual([4,2], utils.parse_version("4-2dls"))

    def test_parse_version_handles_pair_case_with_numbered_suffix(self):
        self.assertListEqual([4,2,7], utils.parse_version("4-2dls7"))

    def test_parse_version_handles_prefixed_case(self):
        self.assertListEqual([2,3], utils.parse_version("dls2-3"))

    def test_parse_version_handles_pair_case_with_doubly_numbered_suffix(self):
        self.assertListEqual([4,2,1,1], utils.parse_version("4-2dls1-1"))

    @patch('os.walk')
    def test_get_latest_version_returns_max_for_simple_pair_versions(self, mock_walk):
        mock_walk.return_value = [
            ('/path_to_module', ('3-8', '4-2','4-1'), ('6-2.tar.gz',)),
            ('/path_to_module/3-8', ('88-88'), ('spam', 'eggs')) ]

        latest = utils.get_latest_version('/path_to_module')
        self.assertEqual('4-2', latest)

    @patch('os.walk')
    def test_get_latest_version_returns_max_for_complex_postfix_versions(self, mock_walk):
        mock_walk.return_value = [
            ('/path_to_module', ('6-7-1dls10', '6-7-1dls14', '6-8-1dls3', '6-8-1dls4-1', '6-9dls1',), ('6-8-1dls1.tar.gz',)),
            ('/path_to_module/3-8', ('88-88'), ('spam', 'eggs')) ]

        latest = utils.get_latest_version('/path_to_module')
        self.assertEqual('6-9dls1', latest)


    @patch('os.walk')
    def test_get_latest_version_returns_max_for_simple_mix_variable_length_max_last_versions(self, mock_walk):
        mock_walk.return_value = [
            ('/path_to_module', ('6-7-1', '6-7', '6-8-4-0', '6-8-4-1',), ()),
            ('/path_to_module/3-8', ('88-88'), ('spam', 'eggs')) ]

        latest = utils.get_latest_version('/path_to_module')
        self.assertEqual('6-8-4-1', latest)


    @patch('os.walk')
    def test_get_latest_version_returns_max_for_mix_variable_length_max_first_versions(self, mock_walk):
        mock_walk.return_value = [
            ('/path_to_module', ('6-9-1', '6-7', '6-8-4-0', '6-8-4-1',), ()),
            ('/path_to_module/3-8', ('88-88'), ('spam', 'eggs')) ]

        latest = utils.get_latest_version('/path_to_module')
        self.assertEqual('6-9-1', latest)


if __name__ == '__main__':
    unittest.main()
