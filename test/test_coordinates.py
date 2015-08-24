import unittest
from convert import coordinates


class TestGenerateCoord(unittest.TestCase):

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

    def test_generate_coord_returns_tuple_with_correct_root_area_module_and_version_for_double_modlevel_ioc_path_with_simple_version(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/ioc/a/b/3-2-1")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("ioc", x.area)
        self.assertEqual("a/b", x.module)
        self.assertEqual("3-2-1", x.version)

    def test_generate_coord_returns_tuple_with_correct_root_area_module_and_version_for_double_modlevel_ioc_path_with_no_version(self):
        x = coordinates.from_path("/dls_sw/prod/R3.14.12.3/ioc/a/b")

        self.assertEqual("/dls_sw/prod/R3.14.12.3", x.root)
        self.assertEqual("ioc", x.area)
        self.assertEqual("a/b", x.module)
        self.assertIsNone(x.version)

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

    def test_as_path_raises_ValueError_if_called_on_rootless_coord(self):
        x = coordinates.create_rootless("my_area", "my_module", "my_version")

        try:
            path = coordinates.as_path(x)
            self.fail("Expected ValueError not thrown: %s", path)
        except ValueError:
            self.assertTrue(True)
        except Exception as ex:
            self.fail("Unexpected exception raised", ex)


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

    def test_create_rootless_coord_returns_tuple_containing_passed_area(self):
        x = coordinates.create_rootless("my_area", "my_module", "my_version")

        self.assertEqual("my_area", x.area)

    def test_create_rootless_coord_returns_tuple_containing_passed_module(self):
        x = coordinates.create_rootless("my_area", "my_module", "my_version")

        self.assertEqual("my_module", x.module)

    def test_create_rootless_coord_returns_tuple_containing_passed_version(self):
        x = coordinates.create_rootless("my_area", "my_module", "my_version")

        self.assertEqual("my_version", x.version)

    def test_create_coord_returns_tuple_with_default_None_version(self):
        x = coordinates.create("my_root", "my_area", "my_module")
        self.assertIsNone(x.version)

    def test_update_version_resets_version_if_None(self):
        x = coordinates.create("my_root", "my_area", "my_module")
        y = coordinates.update_version(x, '123-45')
        self.assertEqual('123-45', y.version)

    def test_update_version_resets_version_if_not_None(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")
        y = coordinates.update_version(x, '123-45')
        self.assertEqual('123-45', y.version)

    def test_update_root_sets_root_if_initially_rootless(self):
        x = coordinates.create_rootless("my_area", "my_module", "my_version")
        y = coordinates.update_root(x, 'new_root')
        self.assertEqual('new_root', y.root)

    def test_update_root_sets_root_if_initially_not_rootless(self):
        x = coordinates.create("my_root", "my_area", "my_module", "my_version")
        y = coordinates.update_root(x, 'new_root')
        self.assertEqual('new_root', y.root)


if __name__ == '__main__':
    unittest.main()
