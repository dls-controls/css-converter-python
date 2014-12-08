
from convert.converter import store_symbol, Converter
import unittest
import mock


class SymbolDictionaryTest(unittest.TestCase):

    def test_stores_new_path_dest_in_empty_dictionary(self):
        symbol_dict = {}
        store_symbol("path", "dest", symbol_dict)
        self.assertTrue(symbol_dict.has_key("path"))
        self.assertEqual(symbol_dict["path"], set(["dest"]))

    def test_adds_new_path_dest_in_non_empty_dictionary(self):
        symbol_dict = {"oldkey": set(["oldval"])}
        store_symbol("path", "dest", symbol_dict)

        self.assertDictEqual({"oldkey": set(["oldval"]), "path": set(["dest"])},
                             symbol_dict)

    def test_does_not_store_duplicate_if_same_path_dest(self):
        symbol_dict = {"path": set(["dest"])}
        store_symbol("path", "dest", symbol_dict)

        self.assertDictEqual({"path": set(["dest"])}, symbol_dict)

    def test_does_append_new_dest_for_existing_key(self):
        symbol_dict = {"path": set(["dest"])}
        store_symbol("path", "new_dest", symbol_dict)

        self.assertDictEqual({"path": set(["dest", "new_dest"])}, symbol_dict)


class DepthTest(unittest.TestCase):

    def test_depths_data(self):
        test_dir = '/dls_sw/prod/R3.14.12.3/ioc/SV/SV-CS-IOC-01/2-1-1/data'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 3)

    def test_depths_ops(self):
        test_dir = '/home/ops/scripts/ops_edl/ResidualKick'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 0)

    def test_depths_tmbf(self):
        '''
        1 from TMBF, 2 from opi/tmbf.
        '''
        test_dir = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi/tmbf'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 3)

    def test_depths_diagOpi_shared(self):
        test_dir = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-45/shared/'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 2)

    def test_depths_diagOpi_root(self):
        '''
        1 from diagOpi.
        '''
        test_dir = '/dls_sw/prod/R3.14.12.3/support/diagOpi/2-45'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 1)

    def test_depths_CS_CS(self):
        '''
        2 from CS/CS-TI-IOC-01, and 1 from data.
        '''
        test_dir = '/dls_sw/work/R3.14.12.3/ioc/CS/CS-TI-IOC-01/data'
        from convert import paths
        paths.index_paths = mock.MagicMock()
        c = Converter([test_dir], [], '/tmp')
        self.assertEqual(c._get_depth(test_dir), 3)

if __name__ == '__main__':
    unittest.main()
