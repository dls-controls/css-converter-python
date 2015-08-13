import unittest
from convert import coordinates


class TestDescriptors(unittest.TestCase):


    def test_generate_coord_returns_tuple_with_correct_root_area_and_module_for_modlevel_support_path(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/support/mirror")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("support", x.area)
        self.assertEqual("mirror", x.module)
        self.assertIsNone(x.version)

    def test_generate_coord_returns_tuple_with_correct_root_area_module_and_version_for_modlevel_support_path_with_simple_version(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/support/modulename/2-6")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("support", x.area)
        self.assertEqual("modulename", x.module)
        self.assertEqual("2-6", x.version)

    def test_generate_coord_returns_tuple_with_correct_root_area_module_and_version_for_modlevel_ioc_path_with_simple_version(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/ioc/othermod/3-2-1")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("ioc", x.area)
        self.assertEqual("othermod", x.module)
        self.assertEqual("3-2-1", x.version)

    def test_generate_coord_returns_tuple_with_correct_data_for_modlevel_ioc_path_with_simple_version_and_edl_file(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/support/mirror/4-7-3/data/mirrorKBM-I22-HFM.edl")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("support", x.area)
        self.assertEqual("mirror", x.module)
        self.assertEqual("4-7-3", x.version)

class TestCoordinatePaths(unittest.TestCase):

    def test_as_path_returns_full_path_if_version_specified(self):
        x = coordinates.create("/my_root", "my_area", "my_module", "my_version")
        path = coordinates.as_path(x)

        self.assertEqual("/my_root/my_area/my_module/my_version", path)

    def test_as_path_returns_full_path_if_version_not_specified(self):
        x = coordinates.create("/my_root", "my_area", "my_module")
        path = coordinates.as_path(x)

        self.assertEqual("/my_root/my_area/my_module", path)

class TestCoordinates(unittest.TestCase):

    def test_create_coord_returns_tuple_containing_passed_root(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")

        self.assertEqual("my_root", x.root)

    def test_create_coord_returns_tuple_containing_passed_area(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")

        self.assertEqual("my_area", x.area)

    def test_create_coord_returns_tuple_containing_passed_module(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")

        self.assertEqual("my_module", x.module)

    def test_create_coord_returns_tuple_containing_passed_version(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")

        self.assertEqual("my_version", x.version)


    def test_create_coord_returns_tuple_with_default_None_version(self):
        x = coordinates.create("my_root", "my_area", "my_module")

        self.assertIsNone(x.version)


