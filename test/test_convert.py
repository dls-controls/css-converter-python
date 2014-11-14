
from convert.converter import store_symbol, is_old_edl
import unittest


class SymbolDictionaryTest(unittest.TestCase):

    def test_stores_new_path_dest_in_empty_dictionary(self):
        symbol_dict = {}
        store_symbol("path", "dest", symbol_dict)
        self.assertTrue(symbol_dict.has_key("path"))
        self.assertListEqual(symbol_dict["path"], ["dest"])

    def test_adds_new_path_dest_in_non_empty_dictionary(self):
        symbol_dict = {"oldkey": ["oldval"]}
        store_symbol("path", "dest", symbol_dict)

        self.assertDictEqual({"oldkey": ["oldval"], "path": ["dest"]},
                             symbol_dict)

    def test_does_not_store_duplicate_if_same_path_dest(self):
        symbol_dict = {"path": ["dest"]}
        store_symbol("path", "dest", symbol_dict)

        self.assertDictEqual({"path": ["dest"]}, symbol_dict)

    def test_does_appends_new_dest_for_existing_key(self):
        symbol_dict = {"path": ["dest"]}
        store_symbol("path", "new_dest", symbol_dict)

        self.assertDictEqual({"path": ["dest", "new_dest"]}, symbol_dict)

class OldEdlTest(unittest.TestCase):

    def test_is_old_edl_recognises_old(self):
        old_edl_file = '/dls_sw/prod/R3.14.11/support/vxStats/1-14/data/FE-IOCs.edl'
        self.assertTrue(is_old_edl(old_edl_file))

    def test_is_old_edl_recognises_new(self):
        new_edl_file = '/dls_sw/prod/R3.14.11/support/vxStats/1-14/data/diamond.edl'
        self.assertFalse(is_old_edl(new_edl_file))

if __name__ == '__main__':
    unittest.main()
