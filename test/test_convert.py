
from convert.converter import store_symbol
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

