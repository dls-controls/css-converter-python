from pkg_resources import require
require('mock')
require('dls_css_utils')

from convert.converter import Converter
import unittest
import mock


class DepthTest(unittest.TestCase):

    def test_depths_data(self):
        test_dir = '/dls_sw/prod/R3.14.12.3/ioc/SV/SV-CS-IOC-01/2-1-1/data'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp', {})
        self.assertEqual(c._get_depth(test_dir), 3)

    def test_depths_tmbf(self):
        '''
        1 from TMBF, 2 from opi/tmbf.
        '''
        test_dir = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi/tmbf'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp', {})
        self.assertEqual(c._get_depth(test_dir), 3)

    def test_depths_diagOpi_shared(self):
        test_dir = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-45/shared/'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp', {})
        self.assertEqual(c._get_depth(test_dir), 2)

    def test_depths_diagOpi_root(self):
        '''
        1 from diagOpi.
        '''
        test_dir = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-45'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp', {})
        self.assertEqual(c._get_depth(test_dir), 1)

    def test_depths_CS_CS(self):
        '''
        2 from CS/CS-TI-IOC-01, and 1 from data.
        '''
        test_dir = '/dls_sw/work/R3.14.12.3/ioc/CS/CS-TI-IOC-01/data'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp', {})
        self.assertEqual(c._get_depth(test_dir), 3)


if __name__ == '__main__':
    unittest.main()
